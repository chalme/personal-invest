from __future__ import annotations

from typing import Any

from app.repositories.sqlite import get_connection


class StockFinancialService:
    def latest(self, symbol: str) -> dict[str, Any]:
        with get_connection() as conn:
            statement = conn.execute(
                """
                SELECT * FROM financial_statement_snapshot
                WHERE symbol = ?
                ORDER BY data_date DESC, id DESC
                LIMIT 1
                """,
                (symbol,),
            ).fetchone()
            metric = conn.execute(
                """
                SELECT * FROM financial_metric_snapshot
                WHERE symbol = ?
                ORDER BY data_date DESC, id DESC
                LIMIT 1
                """,
                (symbol,),
            ).fetchone()
            valuation = conn.execute(
                """
                SELECT * FROM valuation_snapshot
                WHERE symbol = ?
                ORDER BY data_date DESC, id DESC
                LIMIT 1
                """,
                (symbol,),
            ).fetchone()
            quality = conn.execute(
                """
                SELECT * FROM stock_quality_snapshot
                WHERE symbol = ?
                ORDER BY data_date DESC, id DESC
                LIMIT 1
                """,
                (symbol,),
            ).fetchone()
        return {
            "symbol": symbol,
            "statement": dict(statement) if statement else None,
            "metrics": dict(metric) if metric else None,
            "valuation": dict(valuation) if valuation else None,
            "quality": dict(quality) if quality else None,
        }

    def latest_all(self, limit: int = 50) -> list[dict[str, Any]]:
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT q.*
                FROM stock_quality_snapshot q
                JOIN (
                    SELECT symbol, MAX(quality_date) AS quality_date
                    FROM stock_quality_snapshot
                    GROUP BY symbol
                ) latest ON latest.symbol = q.symbol AND latest.quality_date = q.quality_date
                ORDER BY q.total_score DESC, q.symbol ASC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]
