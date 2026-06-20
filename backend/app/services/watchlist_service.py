from datetime import datetime

from app.core.asset_type import infer_asset_type
from app.repositories.sqlite_repo import SQLiteRepository
from app.services.instrument_service import InstrumentService


class WatchlistService:
    def __init__(self, repo: SQLiteRepository | None = None) -> None:
        self.repo = repo or SQLiteRepository()
        self.instruments = InstrumentService(self.repo)

    def list_items(self, asset_type: str | None = None) -> list[dict]:
        sql = """
            SELECT
                w.id,
                w.symbol,
                COALESCE(i.name, w.name) AS name,
                COALESCE(i.asset_type, w.asset_type) AS asset_type,
                COALESCE(i.market, w.market) AS market,
                w.group_name,
                i.sector_code,
                COALESCE(i.sector_name, w.group_name) AS sector_name,
                i.exchange,
                i.fund_type,
                i.risk_level,
                w.reason,
                w.priority,
                w.status,
                w.created_at,
                w.updated_at
            FROM watchlist w
            LEFT JOIN instrument i ON i.symbol = w.symbol
            WHERE w.status = 'ACTIVE'
        """
        if asset_type:
            return self.repo.fetch_all(
                sql + " AND COALESCE(i.asset_type, w.asset_type) = ? ORDER BY w.priority DESC, w.id DESC",
                (asset_type.upper(),),
            )
        return self.repo.fetch_all(sql + " ORDER BY w.priority DESC, w.id DESC")

    def add_item(self, payload: dict) -> int:
        now = datetime.now().isoformat(timespec="seconds")
        asset_type = infer_asset_type(payload["symbol"], payload.get("market"), payload.get("asset_type"))
        row_id = self.repo.execute(
            """
            INSERT INTO watchlist(symbol, name, asset_type, market, group_name, reason, priority, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?, ?)
            ON CONFLICT(symbol) DO UPDATE SET
                name = excluded.name,
                asset_type = excluded.asset_type,
                market = excluded.market,
                group_name = excluded.group_name,
                reason = excluded.reason,
                priority = excluded.priority,
                status = 'ACTIVE',
                updated_at = excluded.updated_at
            """,
            (
                payload["symbol"],
                payload.get("name", payload["symbol"]),
                asset_type,
                payload.get("market", "A_SHARE"),
                payload.get("group_name"),
                payload.get("reason"),
                int(payload.get("priority") or 0),
                now,
                now,
            ),
        )
        self.instruments.upsert(
            symbol=payload["symbol"],
            name=payload.get("name", payload["symbol"]),
            asset_type=asset_type,
            market=payload.get("market", "A_SHARE"),
            sector_name=payload.get("group_name"),
            source="WATCHLIST",
        )
        return row_id

    def remove_item(self, symbol: str) -> None:
        now = datetime.now().isoformat(timespec="seconds")
        self.repo.execute(
            """
            UPDATE watchlist
            SET status = 'REMOVED', updated_at = ?
            WHERE symbol = ?
            """,
            (now, symbol),
        )
