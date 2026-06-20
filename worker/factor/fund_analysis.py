from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from worker.storage import connect_db, now_iso, read_parquet_dataset, upsert_many


@dataclass(frozen=True)
class FundMetrics:
    return_1m: float | None
    return_3m: float | None
    return_6m: float | None
    max_drawdown: float | None
    volatility: float | None
    trend_score: float
    risk_score: float
    total_score: float
    state: str
    conclusion: str
    risk_note: str


def _pct_return(series: pd.Series, periods: int) -> float | None:
    clean = series.dropna()
    if len(clean) <= periods:
        return None
    start = float(clean.iloc[-periods - 1])
    end = float(clean.iloc[-1])
    if start <= 0:
        return None
    return round((end / start) - 1, 4)


def _max_drawdown(series: pd.Series) -> float | None:
    clean = series.dropna().astype(float)
    if len(clean) < 2:
        return None
    peak = clean.cummax()
    drawdown = clean / peak - 1
    return round(float(drawdown.min()), 4)


def _volatility(series: pd.Series) -> float | None:
    clean = series.dropna().astype(float)
    returns = clean.pct_change().dropna()
    if returns.empty:
        return None
    return round(float(returns.std() * (252 ** 0.5)), 4)


def _score_return(value: float | None, neutral: float = 50.0) -> float:
    if value is None:
        return neutral
    return max(0.0, min(100.0, 50.0 + value * 250.0))


def _score_risk(drawdown: float | None, volatility: float | None) -> float:
    drawdown_penalty = abs(drawdown or 0.0) * 180.0
    volatility_penalty = (volatility or 0.0) * 80.0
    return max(0.0, min(100.0, 100.0 - drawdown_penalty - volatility_penalty))


def _state(total_score: float) -> str:
    if total_score >= 78:
        return "强势观察"
    if total_score >= 65:
        return "稳健观察"
    if total_score >= 50:
        return "中性观察"
    return "谨慎观察"


def _build_notes(state: str, ret_3m: float | None, drawdown: float | None, volatility: float | None) -> tuple[str, str]:
    ret_text = "近三个月收益数据不足" if ret_3m is None else f"近三个月收益 {ret_3m:.2%}"
    dd_text = "回撤数据不足" if drawdown is None else f"最大回撤 {drawdown:.2%}"
    vol_text = "波动率数据不足" if volatility is None else f"年化波动 {volatility:.2%}"
    conclusion = f"基金处于{state}状态，{ret_text}。"
    risk_note = f"风险侧重点：{dd_text}，{vol_text}。"
    return conclusion, risk_note


def _calculate_metrics(group: pd.DataFrame) -> FundMetrics:
    nav = group.sort_values("nav_date")["nav"].astype(float)
    ret_1m = _pct_return(nav, 21)
    ret_3m = _pct_return(nav, 63)
    ret_6m = _pct_return(nav, 126)
    drawdown = _max_drawdown(nav)
    volatility = _volatility(nav)
    trend_score = round((_score_return(ret_1m) * 0.35) + (_score_return(ret_3m) * 0.45) + (_score_return(ret_6m) * 0.20), 2)
    risk_score = round(_score_risk(drawdown, volatility), 2)
    total_score = round((trend_score * 0.65) + (risk_score * 0.35), 2)
    state = _state(total_score)
    conclusion, risk_note = _build_notes(state, ret_3m, drawdown, volatility)
    return FundMetrics(
        return_1m=ret_1m,
        return_3m=ret_3m,
        return_6m=ret_6m,
        max_drawdown=drawdown,
        volatility=volatility,
        trend_score=trend_score,
        risk_score=risk_score,
        total_score=total_score,
        state=state,
        conclusion=conclusion,
        risk_note=risk_note,
    )


def calculate_fund_analysis() -> dict[str, Any]:
    df = read_parquet_dataset("fund_nav")
    if df.empty:
        return {"status": "skipped", "count": 0, "latest_nav_date": None}

    required = {"symbol", "name", "nav_date", "nav"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"fund_nav 缺少字段: {', '.join(sorted(missing))}")

    df = df.copy()
    df["nav_date"] = pd.to_datetime(df["nav_date"]).dt.date.astype(str)
    latest_nav_date = str(df["nav_date"].max())
    now = now_iso()
    values: list[tuple[Any, ...]] = []

    for symbol, group in df.groupby("symbol"):
        group = group.sort_values("nav_date")
        latest = group.iloc[-1]
        metrics = _calculate_metrics(group)
        values.append((
            latest_nav_date,
            str(symbol),
            str(latest.get("name") or symbol),
            metrics.total_score,
            metrics.state,
            metrics.return_1m,
            metrics.return_3m,
            metrics.return_6m,
            metrics.max_drawdown,
            metrics.volatility,
            metrics.trend_score,
            metrics.risk_score,
            metrics.conclusion,
            metrics.risk_note,
            f"fund_nav_{latest_nav_date}",
            now,
        ))

    with connect_db() as conn:
        count = upsert_many(
            conn,
            """
            INSERT INTO fund_analysis_snapshot(
                nav_date, symbol, name, total_score, state, return_1m, return_3m, return_6m,
                max_drawdown, volatility, trend_score, risk_score, conclusion, risk_note, data_version, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(nav_date, symbol) DO UPDATE SET
                name = excluded.name,
                total_score = excluded.total_score,
                state = excluded.state,
                return_1m = excluded.return_1m,
                return_3m = excluded.return_3m,
                return_6m = excluded.return_6m,
                max_drawdown = excluded.max_drawdown,
                volatility = excluded.volatility,
                trend_score = excluded.trend_score,
                risk_score = excluded.risk_score,
                conclusion = excluded.conclusion,
                risk_note = excluded.risk_note,
                data_version = excluded.data_version,
                created_at = excluded.created_at
            """,
            values,
        )
    return {"status": "ok", "count": count, "latest_nav_date": latest_nav_date}
