from __future__ import annotations

from pathlib import Path
from typing import Any

import duckdb

from app.core.config import get_settings


class PriceService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.daily_bar_glob = self.settings.data_dir / "parquet" / "daily_bar" / "**" / "*.parquet"

    def latest_bars(self, symbol: str, limit: int = 120) -> list[dict[str, Any]]:
        limit = max(1, min(limit, 500))
        parquet_path = self._parquet_glob()
        if parquet_path is None:
            return []

        sql = """
            SELECT
                CAST(trade_date AS VARCHAR) AS trade_date,
                symbol,
                name,
                open,
                high,
                low,
                close,
                volume,
                amount,
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

    def _parquet_glob(self) -> str | None:
        base = self.settings.data_dir / "parquet" / "daily_bar"
        if not base.exists():
            return None
        if not any(base.rglob("*.parquet")):
            return None
        return str(self.daily_bar_glob)
