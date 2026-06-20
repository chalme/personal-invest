from datetime import datetime

from app.core.asset_type import infer_asset_type
from app.repositories.sqlite_repo import SQLiteRepository


class WatchlistService:
    def __init__(self, repo: SQLiteRepository | None = None) -> None:
        self.repo = repo or SQLiteRepository()

    def list_items(self) -> list[dict]:
        return self.repo.fetch_all(
            "SELECT * FROM watchlist WHERE status = 'ACTIVE' ORDER BY priority DESC, id DESC"
        )

    def add_item(self, payload: dict) -> int:
        now = datetime.now().isoformat(timespec="seconds")
        asset_type = infer_asset_type(payload["symbol"], payload.get("market"), payload.get("asset_type"))
        return self.repo.execute(
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

