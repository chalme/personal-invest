from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

import pandas as pd

from worker.storage import connect_db, now_iso, read_parquet_dataset

HORIZONS = {"1D": 1, "1W": 7, "1M": 30}


def _date_text(value: str | None) -> str | None:
    if not value:
        return None
    return str(value)[:10]


def _price_series(symbol: str, asset_type: str) -> pd.DataFrame:
    if asset_type.upper() == "FUND":
        df = read_parquet_dataset("fund_nav")
        if df.empty:
            return pd.DataFrame(columns=["date", "price"])
        subset = df[df["symbol"] == symbol].copy()
        if subset.empty:
            return pd.DataFrame(columns=["date", "price"])
        subset["date"] = subset["nav_date"].astype(str)
        subset["price"] = pd.to_numeric(subset["nav"], errors="coerce")
        return subset[["date", "price"]].dropna().sort_values("date")
    df = read_parquet_dataset("daily_bar")
    if df.empty:
        return pd.DataFrame(columns=["date", "price"])
    subset = df[df["symbol"] == symbol].copy()
    if subset.empty:
        return pd.DataFrame(columns=["date", "price"])
    subset["date"] = subset["trade_date"].astype(str)
    subset["price"] = pd.to_numeric(subset["close"], errors="coerce")
    return subset[["date", "price"]].dropna().sort_values("date")


def _price_on_or_before(series: pd.DataFrame, target_date: str) -> tuple[str | None, float | None]:
    if series.empty:
        return None, None
    subset = series[series["date"] <= target_date]
    if subset.empty:
        return None, None
    row = subset.iloc[-1]
    return str(row["date"]), float(row["price"])


def _advice_level(conn, symbol: str, target_date: str) -> str | None:
    row = conn.execute(
        """
        SELECT advice_level FROM investment_advice
        WHERE symbol = ? AND advice_date <= ?
        ORDER BY advice_date DESC, id DESC
        LIMIT 1
        """,
        (symbol, target_date),
    ).fetchone()
    return row["advice_level"] if row else None


def _risk_count(conn, symbol: str, target_date: str) -> int:
    row = conn.execute(
        """
        SELECT COUNT(*) AS count FROM risk_event
        WHERE symbol = ? AND trade_date <= ? AND risk_type != 'NO_MAJOR_RISK'
        """,
        (symbol, target_date),
    ).fetchone()
    return int(row["count"] or 0) if row else 0


def refresh_decision_outcomes(as_of: date | None = None) -> dict[str, int]:
    today = as_of or date.today()
    now = now_iso()
    with connect_db() as conn:
        decisions = conn.execute("SELECT * FROM decision_record ORDER BY decision_date ASC, id ASC").fetchall()
    inserted = 0
    considered = 0
    for decision in decisions:
        symbol = str(decision["symbol"])
        asset_type = str(decision["asset_type"] or "STOCK")
        decision_date_text = _date_text(decision["decision_date"])
        if not decision_date_text:
            continue
        decision_date = datetime.fromisoformat(decision_date_text).date()
        series = _price_series(symbol, asset_type)
        decision_price_date, price_at_decision = _price_on_or_before(series, decision_date_text)
        with connect_db() as conn:
            advice_at_decision = decision["advice_level"] or _advice_level(conn, symbol, decision_date_text)
            risk_at_decision = _risk_count(conn, symbol, decision_date_text)
        for horizon, days in HORIZONS.items():
            target = decision_date + timedelta(days=days)
            if target > today:
                continue
            considered += 1
            measured_at, price_at_measure = _price_on_or_before(series, target.isoformat())
            return_ratio = None
            if price_at_decision and price_at_measure:
                return_ratio = (price_at_measure - price_at_decision) / price_at_decision
            with connect_db() as conn:
                advice_at_measure = _advice_level(conn, symbol, measured_at or target.isoformat())
                risk_at_measure = _risk_count(conn, symbol, measured_at or target.isoformat())
            if price_at_decision is None or price_at_measure is None:
                summary = f"{horizon} 复盘缺少价格/净值数据，仅保留决策记录。"
            else:
                summary = f"{horizon} 后价格/净值变化 {return_ratio:.2%}。该结果仅供复盘参考，不代表决策绝对对错。"
            with connect_db() as conn:
                before = conn.total_changes
                conn.execute(
                    """
                    INSERT INTO decision_outcome(
                        decision_id, horizon, measured_at, price_at_decision, price_at_measure,
                        return_ratio, advice_level_at_decision, advice_level_at_measure,
                        risk_count_at_decision, risk_count_at_measure, summary, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(decision_id, horizon) DO UPDATE SET
                        measured_at = excluded.measured_at,
                        price_at_decision = excluded.price_at_decision,
                        price_at_measure = excluded.price_at_measure,
                        return_ratio = excluded.return_ratio,
                        advice_level_at_decision = excluded.advice_level_at_decision,
                        advice_level_at_measure = excluded.advice_level_at_measure,
                        risk_count_at_decision = excluded.risk_count_at_decision,
                        risk_count_at_measure = excluded.risk_count_at_measure,
                        summary = excluded.summary
                    """,
                    (
                        decision["id"],
                        horizon,
                        measured_at or target.isoformat(),
                        price_at_decision,
                        price_at_measure,
                        return_ratio,
                        advice_at_decision,
                        advice_at_measure,
                        risk_at_decision,
                        risk_at_measure,
                        summary,
                        now,
                    ),
                )
                if conn.total_changes > before:
                    inserted += 1
    return {"decisions": len(decisions), "considered": considered, "upserted": inserted}


if __name__ == "__main__":
    print(refresh_decision_outcomes())
