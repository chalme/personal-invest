from __future__ import annotations

from typing import Any

from app.repositories.sqlite_repo import SQLiteRepository


class EtfDeepService:
    def __init__(self, repo: SQLiteRepository | None = None) -> None:
        self.repo = repo or SQLiteRepository()

    def latest(self, symbol: str) -> dict[str, Any]:
        profile = self.repo.fetch_one("SELECT * FROM etf_profile WHERE symbol = ?", (symbol,))
        exposures = self.repo.fetch_all(
            """
            SELECT * FROM etf_exposure_snapshot
            WHERE symbol = ?
              AND snapshot_date = (SELECT MAX(snapshot_date) FROM etf_exposure_snapshot WHERE symbol = ?)
            ORDER BY exposure_type ASC, weight DESC
            """,
            (symbol, symbol),
        )
        liquidity = self.repo.fetch_one(
            """
            SELECT * FROM etf_liquidity_snapshot
            WHERE symbol = ?
            ORDER BY snapshot_date DESC, id DESC
            LIMIT 1
            """,
            (symbol,),
        )
        risk_return = self.repo.fetch_one(
            """
            SELECT * FROM etf_risk_return_snapshot
            WHERE symbol = ?
            ORDER BY snapshot_date DESC, id DESC
            LIMIT 1
            """,
            (symbol,),
        )
        tracking = self.repo.fetch_one(
            """
            SELECT * FROM etf_tracking_snapshot
            WHERE symbol = ?
            ORDER BY snapshot_date DESC, id DESC
            LIMIT 1
            """,
            (symbol,),
        )
        return {
            "symbol": symbol,
            "profile": profile,
            "exposures": exposures,
            "liquidity": liquidity,
            "risk_return": risk_return,
            "tracking": tracking,
        }

    def latest_all(self, limit: int = 50) -> list[dict[str, Any]]:
        return self.repo.fetch_all(
            """
            SELECT r.*
            FROM etf_risk_return_snapshot r
            JOIN (
                SELECT symbol, MAX(snapshot_date) AS snapshot_date
                FROM etf_risk_return_snapshot
                GROUP BY symbol
            ) latest ON latest.symbol = r.symbol AND latest.snapshot_date = r.snapshot_date
            ORDER BY r.risk_return_score DESC, r.symbol ASC
            LIMIT ?
            """,
            (limit,),
        )
