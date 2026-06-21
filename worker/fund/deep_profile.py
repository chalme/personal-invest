from __future__ import annotations

from typing import Any

import pandas as pd

from worker.storage import connect_db, now_iso, read_parquet_dataset, upsert_many


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
    return round(float(returns.std() * (252 ** 0.5)), 4)


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


def build_fund_profile_and_risk_return() -> dict[str, Any]:
    funds = _fund_assets()
    if not funds:
        return {"status": "skipped", "count": 0, "reason": "no active FUND assets"}
    nav_df = read_parquet_dataset("fund_nav")
    if nav_df.empty:
        nav_df = pd.DataFrame(columns=["symbol", "name", "nav_date", "nav"])
    now = now_iso()
    today = now[:10]
    profile_rows: list[tuple[Any, ...]] = []
    manager_rows: list[tuple[Any, ...]] = []
    company_rows: list[tuple[Any, ...]] = []
    risk_rows: list[tuple[Any, ...]] = []
    for fund in funds:
        symbol = str(fund["symbol"])
        name = str(fund.get("name") or symbol)
        fund_type = str(fund.get("fund_type") or "ACTIVE_EQUITY")
        risk_level = str(fund.get("risk_level") or "MEDIUM")
        manager = f"{name}基金经理"
        company = "样本基金公司"
        source_mode = "SAMPLE"
        profile_rows.append((symbol, name, fund_type, risk_level, manager, company, "待补充基准", "费率以基金合同为准", "built_in_sample", source_mode, today, f"fund_profile_{today}_{now}", now))
        manager_rows.append((manager, company, 3.0, "样本经理画像，仅用于字段占位和流程验证。", "built_in_sample", source_mode, today, now))
        company_rows.append((company, "样本规模信息，待接入真实数据源。", "样本风控说明，待接入真实数据源。", "built_in_sample", source_mode, today, now))
        group = nav_df[nav_df.get("symbol", pd.Series(dtype=str)).astype(str) == symbol].copy() if not nav_df.empty else pd.DataFrame()
        if group.empty:
            risk_rows.append((today, symbol, name, None, None, None, None, None, None, None, None, 45.0, "暂无净值序列，暂只能保留基金画像，风险收益等待数据补齐。", "missing_nav", "MISSING", today, f"fund_risk_return_missing_{today}_{now}", now))
            continue
        group = group.sort_values("nav_date")
        nav = pd.to_numeric(group["nav"], errors="coerce")
        ret_1m = _pct(nav, 21)
        ret_3m = _pct(nav, 63)
        ret_6m = _pct(nav, 126)
        drawdown = _max_drawdown(nav)
        volatility = _vol(nav)
        returns = nav.pct_change().dropna()
        sharpe = round(float((returns.mean() * 252) / (returns.std() * (252 ** 0.5))), 4) if len(returns) > 1 and returns.std() else None
        calmar = round(float((ret_6m or 0) / abs(drawdown)), 4) if drawdown else None
        recovery_days = _recovery_days(nav)
        score = _score(ret_3m, drawdown, volatility)
        experience = "持有体验较稳" if score >= 65 else "持有体验中性" if score >= 45 else "持有体验承压"
        latest_date = str(group["nav_date"].max())
        risk_rows.append((latest_date, symbol, name, ret_1m, ret_3m, ret_6m, drawdown, volatility, sharpe, calmar, recovery_days, score, experience, "fund_nav", "REAL", latest_date, f"fund_risk_return_{latest_date}_{now}", now))
    with connect_db() as conn:
        profile_count = upsert_many(conn, """
            INSERT INTO fund_profile(symbol, name, fund_type, risk_level, manager_name, company_name, benchmark, fee_note, source, source_mode, data_date, data_version, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(symbol) DO UPDATE SET
                name=excluded.name,
                fund_type=excluded.fund_type,
                risk_level=excluded.risk_level,
                manager_name=excluded.manager_name,
                company_name=excluded.company_name,
                benchmark=excluded.benchmark,
                fee_note=excluded.fee_note,
                source=excluded.source,
                source_mode=excluded.source_mode,
                data_date=excluded.data_date,
                data_version=excluded.data_version,
                updated_at=excluded.updated_at
        """, profile_rows)
        manager_count = upsert_many(conn, """
            INSERT INTO fund_manager_profile(manager_name, company_name, tenure_years, style_note, source, source_mode, data_date, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(manager_name) DO UPDATE SET
                company_name=excluded.company_name,
                tenure_years=excluded.tenure_years,
                style_note=excluded.style_note,
                source=excluded.source,
                source_mode=excluded.source_mode,
                data_date=excluded.data_date,
                updated_at=excluded.updated_at
        """, manager_rows)
        company_count = upsert_many(conn, """
            INSERT INTO fund_company_profile(company_name, scale_note, risk_control_note, source, source_mode, data_date, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(company_name) DO UPDATE SET
                scale_note=excluded.scale_note,
                risk_control_note=excluded.risk_control_note,
                source=excluded.source,
                source_mode=excluded.source_mode,
                data_date=excluded.data_date,
                updated_at=excluded.updated_at
        """, company_rows)
        risk_count = upsert_many(conn, """
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
        """, risk_rows)
    return {"status": "ok", "count": risk_count, "profile_count": profile_count, "manager_count": manager_count, "company_count": company_count, "risk_return_count": risk_count}


if __name__ == "__main__":
    print(build_fund_profile_and_risk_return())
