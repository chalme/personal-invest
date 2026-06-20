from __future__ import annotations

from datetime import datetime
from typing import Any

from app.core.asset_type import infer_asset_type
from app.repositories.sqlite_repo import SQLiteRepository


class InstrumentService:
    def __init__(self, repo: SQLiteRepository | None = None) -> None:
        self.repo = repo or SQLiteRepository()

    def upsert(
        self,
        *,
        symbol: str,
        name: str | None = None,
        asset_type: str | None = None,
        market: str | None = None,
        exchange: str | None = None,
        sector_code: str | None = None,
        sector_name: str | None = None,
        fund_type: str | None = None,
        risk_level: str | None = None,
        status: str = "ACTIVE",
        source: str | None = None,
    ) -> None:
        now = datetime.now().isoformat(timespec="seconds")
        normalized_asset_type = infer_asset_type(symbol, market, asset_type)
        display_name = name or symbol
        self.repo.execute(
            """
            INSERT INTO instrument(
                symbol, name, asset_type, market, exchange, sector_code, sector_name,
                fund_type, risk_level, status, source, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(symbol) DO UPDATE SET
                name = COALESCE(NULLIF(excluded.name, ''), instrument.name),
                asset_type = excluded.asset_type,
                market = COALESCE(excluded.market, instrument.market),
                exchange = COALESCE(excluded.exchange, instrument.exchange),
                sector_code = COALESCE(excluded.sector_code, instrument.sector_code),
                sector_name = COALESCE(excluded.sector_name, instrument.sector_name),
                fund_type = COALESCE(excluded.fund_type, instrument.fund_type),
                risk_level = COALESCE(excluded.risk_level, instrument.risk_level),
                status = COALESCE(excluded.status, instrument.status),
                source = COALESCE(excluded.source, instrument.source),
                updated_at = excluded.updated_at
            """,
            (
                symbol,
                display_name,
                normalized_asset_type,
                market,
                exchange,
                sector_code,
                sector_name,
                fund_type,
                risk_level,
                status,
                source,
                now,
                now,
            ),
        )

    def by_symbols(self, symbols: list[str]) -> dict[str, dict[str, Any]]:
        if not symbols:
            return {}
        placeholders = ", ".join(["?"] * len(symbols))
        rows = self.repo.fetch_all(
            f"SELECT * FROM instrument WHERE symbol IN ({placeholders})",
            tuple(symbols),
        )
        return {str(row["symbol"]): row for row in rows}
