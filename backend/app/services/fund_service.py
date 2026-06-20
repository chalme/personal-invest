from __future__ import annotations

from typing import Any

import duckdb

from app.core.config import get_settings
from app.repositories.sqlite_repo import SQLiteRepository


class FundService:
    def __init__(self, repo: SQLiteRepository | None = None) -> None:
        self.repo = repo or SQLiteRepository()
        self.settings = get_settings()
        self.fund_nav_glob = self.settings.data_dir / "parquet" / "fund_nav" / "**" / "*.parquet"
        self.daily_bar_glob = self.settings.data_dir / "parquet" / "daily_bar" / "**" / "*.parquet"

    def latest_analysis(self, symbol: str | None = None) -> list[dict[str, Any]]:
        if symbol:
            return self.repo.fetch_all(
                """
                SELECT * FROM fund_analysis_snapshot
                WHERE symbol = ?
                ORDER BY nav_date DESC, id DESC
                LIMIT 30
                """,
                (symbol,),
            )
        return self.repo.fetch_all(
            """
            SELECT * FROM fund_analysis_snapshot
            WHERE nav_date = (SELECT MAX(nav_date) FROM fund_analysis_snapshot)
            ORDER BY total_score DESC, id DESC
            LIMIT 100
            """
        )

    def latest_nav(self, symbol: str, limit: int = 180) -> list[dict[str, Any]]:
        limit = max(1, min(limit, 1000))
        fund_rows = self._latest_fund_nav(symbol, limit)
        if fund_rows:
            return fund_rows
        return self._latest_price_as_nav(symbol, limit)

    def _latest_fund_nav(self, symbol: str, limit: int) -> list[dict[str, Any]]:
        parquet_path = self._fund_parquet_glob()
        if parquet_path is None:
            return []
        sql = """
            SELECT
                CAST(nav_date AS VARCHAR) AS nav_date,
                symbol,
                name,
                nav,
                accumulated_nav,
                source
            FROM read_parquet(?, hive_partitioning = true)
            WHERE symbol = ?
            ORDER BY nav_date DESC
            LIMIT ?
        """
        with duckdb.connect(database=":memory:", read_only=False) as conn:
            rows = conn.execute(sql, [parquet_path, symbol, limit]).fetchall()
            columns = [desc[0] for desc in conn.description]
        return [dict(zip(columns, row, strict=True)) for row in reversed(rows)]

    def _latest_price_as_nav(self, symbol: str, limit: int) -> list[dict[str, Any]]:
        parquet_path = self._daily_bar_glob()
        if parquet_path is None:
            return []
        sql = """
            SELECT
                CAST(trade_date AS VARCHAR) AS nav_date,
                symbol,
                name,
                close AS nav,
                close AS accumulated_nav,
                source
            FROM read_parquet(?, hive_partitioning = true)
            WHERE symbol = ?
            ORDER BY trade_date DESC
            LIMIT ?
        """
        with duckdb.connect(database=":memory:", read_only=False) as conn:
            rows = conn.execute(sql, [parquet_path, symbol, limit]).fetchall()
            columns = [desc[0] for desc in conn.description]
        return [dict(zip(columns, row, strict=True)) for row in reversed(rows)]

    def _fund_parquet_glob(self) -> str | None:
        base = self.settings.data_dir / "parquet" / "fund_nav"
        if not base.exists() or not any(base.rglob("*.parquet")):
            return None
        return str(self.fund_nav_glob)

    def _daily_bar_glob(self) -> str | None:
        base = self.settings.data_dir / "parquet" / "daily_bar"
        if not base.exists() or not any(base.rglob("*.parquet")):
            return None
        return str(self.daily_bar_glob)
