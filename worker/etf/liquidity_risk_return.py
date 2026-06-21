from __future__ import annotations

from typing import Any

import pandas as pd

from worker.storage import connect_db, now_iso, read_parquet_dataset, upsert_many


def _assets() -> list[dict[str, Any]]:
    with connect_db() as conn:
        rows = conn.execute(
            """
            SELECT symbol, name
            FROM instrument
            WHERE status = 'ACTIVE' AND UPPER(asset_type) IN ('ETF', 'LOF')
            ORDER BY symbol
            """
        ).fetchall()
    return [dict(row) for row in rows]


def _pct(series: pd.Series, periods: int) -> float | None:
    clean = series.dropna().astype(float)
    if len(clean) <= periods:
        return None
    base = float(clean.iloc[-periods - 1])
    if base <= 0:
        return None
    return round(float(clean.iloc[-1] / base - 1), 4)


def _max_dd(series: pd.Series) -> float | None:
    clean = series.dropna().astype(float)
    if len(clean) < 2:
        return None
    return round(float((clean / clean.cummax() - 1).min()), 4)


def _vol(series: pd.Series) -> float | None:
    returns = series.dropna().astype(float).pct_change().dropna()
    if len(returns) < 2:
        return None
    return round(float(returns.std() * (252 ** 0.5)), 4)


def _liq(avg_amount: float | None, avg_volume: float | None) -> tuple[float, str, str]:
    if avg_amount is None or avg_volume is None:
        return 35.0, "UNKNOWN", "缺少成交额或成交量，暂不能形成高置信流动性判断。"
    if avg_amount >= 100_000_000:
        return 85.0, "LOW", "近 20 日成交额较高，交易流动性压力较低。"
    if avg_amount >= 20_000_000:
        return 65.0, "MEDIUM", "近 20 日成交额中等，交易时需要关注冲击成本。"
    return 40.0, "HIGH", "近 20 日成交额偏低，交易时需警惕流动性风险。"


def _rr_score(ret_3m: float | None, drawdown: float | None, volatility: float | None) -> tuple[float, str, str]:
    score = 50 + (ret_3m or 0) * 260 - abs(drawdown or 0) * 180 - (volatility or 0) * 80
    score = round(max(0, min(100, score)), 2)
    if score >= 70:
        return score, "LOW", "阶段收益和回撤表现较稳。"
    if score >= 45:
        return score, "MEDIUM", "阶段表现中性，需要结合跟踪质量和流动性复核。"
    return score, "HIGH", "阶段回撤或波动偏高，需谨慎复核。"


def build_etf_liquidity_risk_return() -> dict[str, Any]:
    assets = _assets()
    if not assets:
        return {"status": "skipped", "count": 0, "reason": "no active ETF or LOF assets"}
    bars = read_parquet_dataset("daily_bar")
    now = now_iso()
    today = now[:10]
    liquidity_rows: list[tuple[Any, ...]] = []
    risk_rows: list[tuple[Any, ...]] = []

    for asset in assets:
        symbol = str(asset["symbol"])
        name = str(asset.get("name") or symbol)
        group = bars[bars.get("symbol", pd.Series(dtype=str)).astype(str) == symbol].copy() if not bars.empty else pd.DataFrame()
        if group.empty:
            version = f"etf_liquidity_missing_{today}_{now}"
            liquidity_rows.append((today, symbol, name, None, None, None, None, None, 35.0, "UNKNOWN", "缺少 ETF 行情成交数据，等待数据源补齐。", "daily_bar", "MISSING", today, version, now))
            risk_rows.append((today, symbol, name, None, None, None, None, None, 35.0, "UNKNOWN", "缺少 ETF 价格序列，暂不能形成高置信风险收益判断。", "daily_bar", "MISSING", today, version, now))
            continue

        group["trade_date"] = group["trade_date"].astype(str)
        group = group.sort_values("trade_date")
        close = pd.to_numeric(group["close"], errors="coerce")
        amount = pd.to_numeric(group.get("amount", pd.Series(dtype=float)), errors="coerce")
        volume = pd.to_numeric(group.get("volume", pd.Series(dtype=float)), errors="coerce")
        latest_date = str(group["trade_date"].iloc[-1])
        source = str(group.get("source", pd.Series(["sample"])).iloc[-1]).lower()
        source_mode = "ESTIMATED" if source == "sample" else "REAL"
        version = f"etf_liquidity_risk_{latest_date}_{now}"

        avg_amount = round(float(amount.tail(20).mean()), 2) if amount.dropna().any() else None
        avg_volume = round(float(volume.tail(20).mean()), 2) if volume.dropna().any() else None
        latest_amount = round(float(amount.iloc[-1]), 2) if len(amount) and pd.notna(amount.iloc[-1]) else None
        latest_volume = round(float(volume.iloc[-1]), 2) if len(volume) and pd.notna(volume.iloc[-1]) else None
        estimated_scale = round(float(avg_amount * 50), 2) if avg_amount is not None else None
        liq_score, liq_level, liq_note = _liq(avg_amount, avg_volume)

        ret_1m = _pct(close, 21)
        ret_3m = _pct(close, 63)
        ret_6m = _pct(close, 126)
        drawdown = _max_dd(close)
        vol = _vol(close)
        rr_score, rr_level, rr_note = _rr_score(ret_3m, drawdown, vol)

        liquidity_rows.append((latest_date, symbol, name, avg_amount, avg_volume, latest_amount, latest_volume, estimated_scale, liq_score, liq_level, liq_note, "daily_bar", source_mode, latest_date, version, now))
        risk_rows.append((latest_date, symbol, name, ret_1m, ret_3m, ret_6m, drawdown, vol, rr_score, rr_level, rr_note, "daily_bar", source_mode, latest_date, version, now))

    with connect_db() as conn:
        liquidity_count = upsert_many(conn, _LIQ_SQL, liquidity_rows)
        risk_count = upsert_many(conn, _RISK_SQL, risk_rows)
    return {"status": "ok", "count": risk_count, "liquidity_count": liquidity_count, "risk_return_count": risk_count}


_LIQ_SQL = """
INSERT INTO etf_liquidity_snapshot(snapshot_date, symbol, name, avg_amount_20, avg_volume_20, latest_amount, latest_volume, estimated_scale, liquidity_score, liquidity_risk_level, liquidity_note, source, source_mode, data_date, data_version, created_at)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(snapshot_date, symbol) DO UPDATE SET
    name=excluded.name,
    avg_amount_20=excluded.avg_amount_20,
    avg_volume_20=excluded.avg_volume_20,
    latest_amount=excluded.latest_amount,
    latest_volume=excluded.latest_volume,
    estimated_scale=excluded.estimated_scale,
    liquidity_score=excluded.liquidity_score,
    liquidity_risk_level=excluded.liquidity_risk_level,
    liquidity_note=excluded.liquidity_note,
    source=excluded.source,
    source_mode=excluded.source_mode,
    data_date=excluded.data_date,
    data_version=excluded.data_version,
    created_at=excluded.created_at
"""


_RISK_SQL = """
INSERT INTO etf_risk_return_snapshot(snapshot_date, symbol, name, return_1m, return_3m, return_6m, max_drawdown, volatility, risk_return_score, risk_level, performance_note, source, source_mode, data_date, data_version, created_at)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(snapshot_date, symbol) DO UPDATE SET
    name=excluded.name,
    return_1m=excluded.return_1m,
    return_3m=excluded.return_3m,
    return_6m=excluded.return_6m,
    max_drawdown=excluded.max_drawdown,
    volatility=excluded.volatility,
    risk_return_score=excluded.risk_return_score,
    risk_level=excluded.risk_level,
    performance_note=excluded.performance_note,
    source=excluded.source,
    source_mode=excluded.source_mode,
    data_date=excluded.data_date,
    data_version=excluded.data_version,
    created_at=excluded.created_at
"""


if __name__ == "__main__":
    print(build_etf_liquidity_risk_return())
