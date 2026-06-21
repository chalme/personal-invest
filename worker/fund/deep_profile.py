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


def _fund_assets() -> list[dict[str, Any]]:
    with connect_db() as conn:
        rows = conn.execute(
            """
            SELECT symbol, name, COALESCE(fund_type, 'ACTIVE_EQUITY') AS fund_type,
                   COALESCE(risk_level, 'MEDIUM') AS risk_level
            FROM instrument
            WHERE status = 'ACTIVE' AND UPPER(asset_type) = 'FUND'
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


def _max_drawdown(series: pd.Series) -> float | None:
    clean = series.dropna().astype(float)
    if len(clean) < 2:
        return None
    return round(float((clean / clean.cummax() - 1).min()), 4)


def _vol(series: pd.Series) -> float | None:
    returns = series.dropna().astype(float).pct_change().dropna()
    if returns.empty:
        return None
    return round(float(returns.std() * (252**0.5)), 4)


def _score(ret_3m: float | None, drawdown: float | None, vol: float | None) -> float:
    ret_component = 50 + (ret_3m or 0) * 260
    risk_penalty = abs(drawdown or 0) * 160 + (vol or 0) * 70
    return round(max(0, min(100, ret_component - risk_penalty)), 2)


def _recovery_days(series: pd.Series) -> int | None:
    clean = series.dropna().astype(float).reset_index(drop=True)
    if len(clean) < 2:
        return None
    peak = clean.cummax()
    drawdown = clean / peak - 1
    trough_idx = int(drawdown.idxmin())
    previous_peak = float(peak.iloc[trough_idx])
    recovered = clean.iloc[trough_idx:][clean.iloc[trough_idx:] >= previous_peak]
    if recovered.empty:
        return None
    return int(recovered.index[0] - trough_idx)


def _missing_risk_row(today: str, now: str, symbol: str, name: str, reason: str) -> tuple[Any, ...]:
    return (
        today,
        symbol,
        name,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        reason,
        "missing_real_nav",
        "MISSING",
        today,
        f"fund_risk_return_missing_{today}_{now}",
        now,
    )


def build_fund_profile_and_risk_return() -> dict[str, Any]:
    funds = _fund_assets()
    if not funds:
        return {"status": "skipped", "count": 0, "reason": "no active FUND assets"}

    nav_df = read_parquet_dataset("fund_nav")
    now = now_iso()
    today = now[:10]
    risk_rows: list[tuple[Any, ...]] = []

    for fund in funds:
        symbol = str(fund["symbol"])
        name = str(fund.get("name") or symbol)
        group = (
            nav_df[nav_df.get("symbol", pd.Series(dtype=str)).astype(str) == symbol].copy()
            if not nav_df.empty
            else pd.DataFrame()
        )
        if group.empty:
            risk_rows.append(
                _missing_risk_row(
                    today, now, symbol, name, "缺少真实基金净值，未生成样本基金画像。"
                )
            )
            continue
        if "source" in group.columns:
            group = group[
                ~group["source"].astype(str).str.lower().isin(NON_REAL_SOURCE_VALUES)
            ].copy()
        if group.empty:
            risk_rows.append(
                _missing_risk_row(
                    today, now, symbol, name, "基金净值命中历史非真实污染，等待清理或真实净值补齐。"
                )
            )
            continue

        group = group.sort_values("nav_date")
        nav = pd.to_numeric(group["nav"], errors="coerce")
        ret_1m = _pct(nav, 21)
        ret_3m = _pct(nav, 63)
        ret_6m = _pct(nav, 126)
        drawdown = _max_drawdown(nav)
        volatility = _vol(nav)
        returns = nav.pct_change().dropna()
        sharpe = (
            round(float((returns.mean() * 252) / (returns.std() * (252**0.5))), 4)
            if len(returns) > 1 and returns.std()
            else None
        )
        calmar = round(float((ret_6m or 0) / abs(drawdown)), 4) if drawdown else None
        recovery_days = _recovery_days(nav)
        score = _score(ret_3m, drawdown, volatility)
        experience = (
            "持有体验较稳" if score >= 65 else "持有体验中性" if score >= 45 else "持有体验承压"
        )
        latest_date = str(group["nav_date"].max())
        risk_rows.append(
            (
                latest_date,
                symbol,
                name,
                ret_1m,
                ret_3m,
                ret_6m,
                drawdown,
                volatility,
                sharpe,
                calmar,
                recovery_days,
                score,
                experience,
                "fund_nav",
                "REAL",
                latest_date,
                f"fund_risk_return_{latest_date}_{now}",
                now,
            )
        )

    with connect_db() as conn:
        risk_count = upsert_many(
            conn,
            """
            INSERT INTO fund_risk_return_snapshot(snapshot_date, symbol, name, return_1m, return_3m, return_6m, max_drawdown, volatility, sharpe, calmar, drawdown_recovery_days, risk_return_score, holding_experience, source, source_mode, data_date, data_version, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(snapshot_date, symbol) DO UPDATE SET
                name=excluded.name,
                return_1m=excluded.return_1m,
                return_3m=excluded.return_3m,
                return_6m=excluded.return_6m,
                max_drawdown=excluded.max_drawdown,
                volatility=excluded.volatility,
                sharpe=excluded.sharpe,
                calmar=excluded.calmar,
                drawdown_recovery_days=excluded.drawdown_recovery_days,
                risk_return_score=excluded.risk_return_score,
                holding_experience=excluded.holding_experience,
                source=excluded.source,
                source_mode=excluded.source_mode,
                data_date=excluded.data_date,
                data_version=excluded.data_version,
                created_at=excluded.created_at
            """,
            risk_rows,
        )
    return {
        "status": "ok",
        "count": risk_count,
        "profile_count": 0,
        "manager_count": 0,
        "company_count": 0,
        "risk_return_count": risk_count,
        "reason": "fund profile/manager/company real source is not connected",
    }


if __name__ == "__main__":
    print(build_fund_profile_and_risk_return())
