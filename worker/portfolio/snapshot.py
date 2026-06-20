from __future__ import annotations

import json
from collections import Counter
from typing import Any

from worker.storage import connect_db, now_iso


def _latest_date(conn, table: str, column: str) -> str | None:
    row = conn.execute(f"SELECT MAX({column}) AS value FROM {table}").fetchone()
    return row["value"] if row else None


def build_portfolio_snapshot(account_id: int = 1) -> dict[str, Any]:
    with connect_db() as conn:
        market_date = _latest_date(conn, "market_trend_snapshot", "trade_date")
        snapshot_date = market_date or now_iso()[:10]
        positions = conn.execute(
            """
            SELECT
                p.symbol,
                COALESCE(i.asset_type, p.asset_type, 'STOCK') AS asset_type,
                p.quantity,
                p.avg_cost,
                p.market_value,
                p.pnl
            FROM portfolio_position p
            LEFT JOIN instrument i ON i.symbol = p.symbol
            WHERE p.account_id = ?
            """,
            (account_id,),
        ).fetchall()
        risk_date = _latest_date(conn, "risk_event", "trade_date")
        risk_count = 0
        if risk_date:
            risk_count = int(conn.execute("SELECT COUNT(*) AS count FROM risk_event WHERE trade_date = ?", (risk_date,)).fetchone()["count"])
        advice_date = _latest_date(conn, "investment_advice", "advice_date")
        advice_rows = []
        if advice_date:
            advice_rows = conn.execute(
                "SELECT advice_level FROM investment_advice WHERE account_id = ? AND advice_date = ?",
                (account_id, advice_date),
            ).fetchall()

        total_market_value = sum(float(row["market_value"] or 0) for row in positions)
        total_cost = sum(float(row["quantity"] or 0) * float(row["avg_cost"] or 0) for row in positions)
        total_pnl = sum(float(row["pnl"] or 0) for row in positions)
        total_pnl_ratio = total_pnl / total_cost if total_cost > 0 else 0.0
        values_by_type = {"STOCK": 0.0, "ETF": 0.0, "FUND": 0.0}
        concentration_hhi = 0.0
        for row in positions:
            value = float(row["market_value"] or 0)
            asset_type = str(row["asset_type"] or "STOCK").upper()
            if asset_type not in values_by_type:
                asset_type = "STOCK"
            values_by_type[asset_type] += value
            weight = value / total_market_value if total_market_value > 0 else 0.0
            concentration_hhi += weight * weight

        advice_counter = Counter(str(row["advice_level"]) for row in advice_rows)
        advice_summary = {
            "advice_date": advice_date,
            "levels": dict(advice_counter),
        }
        now = now_iso()
        conn.execute(
            """
            INSERT INTO portfolio_snapshot(
                snapshot_date, account_id, total_market_value, total_cost, total_pnl, total_pnl_ratio,
                stock_value, etf_value, fund_value, concentration_hhi, risk_count, advice_summary, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(snapshot_date, account_id) DO UPDATE SET
                total_market_value = excluded.total_market_value,
                total_cost = excluded.total_cost,
                total_pnl = excluded.total_pnl,
                total_pnl_ratio = excluded.total_pnl_ratio,
                stock_value = excluded.stock_value,
                etf_value = excluded.etf_value,
                fund_value = excluded.fund_value,
                concentration_hhi = excluded.concentration_hhi,
                risk_count = excluded.risk_count,
                advice_summary = excluded.advice_summary,
                created_at = excluded.created_at
            """,
            (
                snapshot_date,
                account_id,
                round(total_market_value, 2),
                round(total_cost, 2),
                round(total_pnl, 2),
                round(total_pnl_ratio, 6),
                round(values_by_type["STOCK"], 2),
                round(values_by_type["ETF"], 2),
                round(values_by_type["FUND"], 2),
                round(concentration_hhi, 6),
                risk_count,
                json.dumps(advice_summary, ensure_ascii=False),
                now,
            ),
        )
        conn.commit()
    return {"status": "ok", "snapshot_date": snapshot_date, "account_id": account_id, "total_market_value": round(total_market_value, 2)}
