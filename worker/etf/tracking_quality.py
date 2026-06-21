from __future__ import annotations

# ruff: noqa: E501
from typing import Any

import pandas as pd

from worker.storage import connect_db, now_iso, read_parquet_dataset, upsert_many

NON_REAL_SOURCE_VALUES = {
    "sample",
    "estimated",
    "built_in_sample",
    "deterministic_estimate",
    "instrument_estimate",
    "mock",
    "demo",
}


def _profiles() -> list[dict[str, Any]]:
    with connect_db() as conn:
        rows = conn.execute(
            """
            SELECT i.symbol, i.name, p.tracking_index
            FROM instrument i
            LEFT JOIN etf_profile p ON p.symbol = i.symbol
            WHERE i.status = 'ACTIVE' AND UPPER(i.asset_type) IN ('ETF', 'LOF')
            ORDER BY i.symbol
            """
        ).fetchall()
    return [dict(row) for row in rows]


def _index_symbol(tracking_index: str | None) -> str | None:
    text = tracking_index or ""
    if "沪深300" in text:
        return "000300.SH"
    if "中证500" in text:
        return "000905.SH"
    return None


def _quality(score: float | None) -> tuple[str, str]:
    if score is None:
        return "UNKNOWN", "缺少指数或净值数据，暂不能形成高置信跟踪质量判断。"
    if score >= 75:
        return "GOOD", "基于真实价格序列的阶段跟踪拟合较好，后续仍需接入真实净值或 IOPV 复核。"
    if score >= 55:
        return "WATCH", "基于真实价格序列的阶段跟踪拟合中性，需继续观察跟踪偏离。"
    return "WEAK", "基于真实价格序列的阶段跟踪拟合偏弱，后续需重点复核。"


def build_etf_tracking_quality() -> dict[str, Any]:
    profiles = _profiles()
    if not profiles:
        return {"status": "skipped", "count": 0, "reason": "no active ETF or LOF assets"}
    bars = read_parquet_dataset("daily_bar")
    now = now_iso()
    today = now[:10]
    rows: list[tuple[Any, ...]] = []

    for profile in profiles:
        symbol = str(profile["symbol"])
        name = str(profile.get("name") or symbol)
        tracking_index = profile.get("tracking_index")
        index_symbol = _index_symbol(str(tracking_index) if tracking_index else None)
        etf = (
            bars[bars.get("symbol", pd.Series(dtype=str)).astype(str) == symbol].copy()
            if not bars.empty
            else pd.DataFrame()
        )
        index = (
            bars[bars.get("symbol", pd.Series(dtype=str)).astype(str) == index_symbol].copy()
            if index_symbol and not bars.empty
            else pd.DataFrame()
        )
        if etf.empty or index.empty:
            version = f"etf_tracking_missing_{today}_{now}"
            level, note = _quality(None)
            rows.append(
                (
                    today,
                    symbol,
                    name,
                    tracking_index,
                    index_symbol,
                    None,
                    None,
                    None,
                    None,
                    level,
                    note,
                    "daily_bar",
                    "MISSING",
                    today,
                    version,
                    now,
                )
            )
            continue

        etf["trade_date"] = etf["trade_date"].astype(str)
        index["trade_date"] = index["trade_date"].astype(str)
        merged = (
            etf[["trade_date", "close", "source"]]
            .rename(columns={"close": "etf_close", "source": "etf_source"})
            .merge(
                index[["trade_date", "close", "source"]].rename(
                    columns={"close": "index_close", "source": "index_source"}
                ),
                on="trade_date",
                how="inner",
            )
            .sort_values("trade_date")
        )
        if len(merged) < 30:
            version = f"etf_tracking_missing_{today}_{now}"
            level, note = _quality(None)
            rows.append(
                (
                    today,
                    symbol,
                    name,
                    tracking_index,
                    index_symbol,
                    None,
                    None,
                    None,
                    None,
                    level,
                    "可比价格序列不足 30 日，暂不能形成高置信跟踪质量判断。",
                    "daily_bar",
                    "MISSING",
                    today,
                    version,
                    now,
                )
            )
            continue

        if (
            str(merged["etf_source"].iloc[-1]).lower() in NON_REAL_SOURCE_VALUES
            or str(merged["index_source"].iloc[-1]).lower() in NON_REAL_SOURCE_VALUES
        ):
            version = f"etf_tracking_missing_{today}_{now}"
            level, _ = _quality(None)
            rows.append(
                (
                    today,
                    symbol,
                    name,
                    tracking_index,
                    index_symbol,
                    None,
                    None,
                    None,
                    None,
                    level,
                    "ETF 或指数价格序列命中历史非真实污染，等待清理或真实行情补齐。",
                    "daily_bar",
                    "MISSING",
                    today,
                    version,
                    now,
                )
            )
            continue

        etf_close = pd.to_numeric(merged["etf_close"], errors="coerce")
        index_close = pd.to_numeric(merged["index_close"], errors="coerce")
        etf_ret = etf_close.pct_change().dropna()
        index_ret = index_close.pct_change().dropna()
        diff = (etf_ret - index_ret).dropna()
        tracking_error = round(float(diff.std() * (252**0.5)), 4) if len(diff) > 2 else None
        tracking_deviation = round(
            float(
                (etf_close.iloc[-1] / etf_close.iloc[0] - 1)
                - (index_close.iloc[-1] / index_close.iloc[0] - 1)
            ),
            4,
        )
        fit_score = round(
            max(0, min(100, 85 - abs(tracking_deviation) * 500 - (tracking_error or 0) * 160)), 2
        )
        level, note = _quality(fit_score)
        latest_date = str(merged["trade_date"].iloc[-1])
        source_mode = "REAL"
        version = f"etf_tracking_{latest_date}_{now}"
        rows.append(
            (
                latest_date,
                symbol,
                name,
                tracking_index,
                index_symbol,
                tracking_error,
                tracking_deviation,
                None,
                fit_score,
                level,
                note + " 折溢价依赖真实净值或 IOPV 数据，当前未生成确定性结论。",
                "daily_bar",
                source_mode,
                latest_date,
                version,
                now,
            )
        )

    with connect_db() as conn:
        count = upsert_many(conn, _SQL, rows)
    return {"status": "ok", "count": count}


_SQL = """
INSERT INTO etf_tracking_snapshot(snapshot_date, symbol, name, tracking_index, index_symbol, tracking_error, tracking_deviation, premium_discount, fit_score, tracking_quality_level, tracking_note, source, source_mode, data_date, data_version, created_at)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(snapshot_date, symbol) DO UPDATE SET
    name=excluded.name,
    tracking_index=excluded.tracking_index,
    index_symbol=excluded.index_symbol,
    tracking_error=excluded.tracking_error,
    tracking_deviation=excluded.tracking_deviation,
    premium_discount=excluded.premium_discount,
    fit_score=excluded.fit_score,
    tracking_quality_level=excluded.tracking_quality_level,
    tracking_note=excluded.tracking_note,
    source=excluded.source,
    source_mode=excluded.source_mode,
    data_date=excluded.data_date,
    data_version=excluded.data_version,
    created_at=excluded.created_at
"""


if __name__ == "__main__":
    print(build_etf_tracking_quality())
