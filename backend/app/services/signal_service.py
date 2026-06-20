from __future__ import annotations

from typing import Any

from app.repositories.sqlite_repo import SQLiteRepository


class SignalService:
    def __init__(self, repo: SQLiteRepository | None = None) -> None:
        self.repo = repo or SQLiteRepository()

    def latest_signals(self, limit: int = 100) -> list[dict[str, Any]]:
        limit = max(1, min(limit, 500))
        return self.repo.fetch_all(
            """
            SELECT * FROM strategy_signal
            WHERE trade_date = (SELECT MAX(trade_date) FROM strategy_signal)
            ORDER BY score DESC, id DESC
            LIMIT ?
            """,
            (limit,),
        )

    def signal_history(self, symbol: str, limit: int = 100) -> list[dict[str, Any]]:
        limit = max(1, min(limit, 500))
        return self.repo.fetch_all(
            """
            SELECT * FROM strategy_signal
            WHERE symbol = ?
            ORDER BY trade_date DESC, id DESC
            LIMIT ?
            """,
            (symbol, limit),
        )
