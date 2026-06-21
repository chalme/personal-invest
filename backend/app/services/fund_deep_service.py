from __future__ import annotations

from typing import Any

from app.repositories.sqlite_repo import SQLiteRepository


class FundDeepService:
    def __init__(self, repo: SQLiteRepository | None = None) -> None:
        self.repo = repo or SQLiteRepository()

    def latest(self, symbol: str) -> dict[str, Any]:
        profile = self.repo.fetch_one("SELECT * FROM fund_profile WHERE symbol = ?", (symbol,))
        risk_return = self.repo.fetch_one(
            """
            SELECT * FROM fund_risk_return_snapshot
            WHERE symbol = ?
            ORDER BY snapshot_date DESC, id DESC
            LIMIT 1
            """,
            (symbol,),
        )
        manager = self.repo.fetch_one("SELECT * FROM fund_manager_profile WHERE manager_name = ?", (profile.get("manager_name"),)) if profile else None
        company = self.repo.fetch_one("SELECT * FROM fund_company_profile WHERE company_name = ?", (profile.get("company_name"),)) if profile else None
        benchmark = self.repo.fetch_one("""
            SELECT * FROM fund_benchmark_snapshot
            WHERE symbol = ?
            ORDER BY snapshot_date DESC, id DESC
            LIMIT 1
            """, (symbol,))
        peer = self.repo.fetch_one("""
            SELECT * FROM fund_peer_rank_snapshot
            WHERE symbol = ?
            ORDER BY snapshot_date DESC, id DESC
            LIMIT 1
            """, (symbol,))
        exposures = self.repo.fetch_all("""
            SELECT * FROM fund_holding_exposure_snapshot
            WHERE symbol = ?
              AND snapshot_date = (SELECT MAX(snapshot_date) FROM fund_holding_exposure_snapshot WHERE symbol = ?)
            ORDER BY exposure_type ASC, weight DESC
            """, (symbol, symbol))
        return {"symbol": symbol, "profile": profile, "manager": manager, "company": company, "risk_return": risk_return, "benchmark": benchmark, "peer": peer, "exposures": exposures}

    def latest_all(self, limit: int = 50) -> list[dict[str, Any]]:
        return self.repo.fetch_all(
            """
            SELECT r.*
            FROM fund_risk_return_snapshot r
            JOIN (
                SELECT symbol, MAX(snapshot_date) AS snapshot_date
                FROM fund_risk_return_snapshot
                GROUP BY symbol
            ) latest ON latest.symbol = r.symbol AND latest.snapshot_date = r.snapshot_date
            ORDER BY r.risk_return_score DESC, r.symbol ASC
            LIMIT ?
            """,
            (limit,),
        )
