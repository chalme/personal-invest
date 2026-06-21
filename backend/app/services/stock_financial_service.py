from __future__ import annotations

from typing import Any

from app.repositories.sqlite_repo import SQLiteRepository


class StockFinancialService:
    def __init__(self, repo: SQLiteRepository | None = None) -> None:
        self.repo = repo or SQLiteRepository()

    def latest(self, symbol: str) -> dict[str, Any]:
        statement = self.repo.fetch_one(
            """
            SELECT * FROM financial_statement_snapshot
            WHERE symbol = ?
            ORDER BY data_date DESC, id DESC
            LIMIT 1
            """,
            (symbol,),
        )
        metric = self.repo.fetch_one(
            """
            SELECT * FROM financial_metric_snapshot
            WHERE symbol = ?
            ORDER BY data_date DESC, id DESC
            LIMIT 1
            """,
            (symbol,),
        )
        valuation = self.repo.fetch_one(
            """
            SELECT * FROM valuation_snapshot
            WHERE symbol = ?
            ORDER BY data_date DESC, id DESC
            LIMIT 1
            """,
            (symbol,),
        )
        quality = self.repo.fetch_one(
            """
            SELECT * FROM stock_quality_snapshot
            WHERE symbol = ?
            ORDER BY data_date DESC, id DESC
            LIMIT 1
            """,
            (symbol,),
        )
        return {
            "symbol": symbol,
            "statement": statement,
            "metrics": metric,
            "valuation": valuation,
            "quality": quality,
        }

    def latest_all(self, limit: int = 50) -> list[dict[str, Any]]:
        return self.repo.fetch_all(
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
        )
