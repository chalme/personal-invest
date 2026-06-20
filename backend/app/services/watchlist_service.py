from datetime import datetime

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
        return self.repo.execute(
            """
            INSERT INTO watchlist(symbol, name, market, group_name, reason, priority, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 'ACTIVE', ?, ?)
            ON CONFLICT(symbol) DO UPDATE SET
                name = excluded.name,
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
                payload.get("market", "A_SHARE"),
                payload.get("group_name"),
                payload.get("reason"),
                int(payload.get("priority") or 0),
                now,
                now,
            ),
        )

