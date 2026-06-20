from __future__ import annotations

from app.repositories.sqlite_repo import SQLiteRepository


class DashboardService:
    def __init__(self, repo: SQLiteRepository | None = None) -> None:
        self.repo = repo or SQLiteRepository()

    def get_dashboard(self) -> dict:
        market = self.repo.fetch_one(
            "SELECT * FROM market_trend_snapshot ORDER BY trade_date DESC, id DESC LIMIT 1"
        )
        sectors = self.repo.fetch_all(
            """
            SELECT * FROM sector_trend_snapshot
            WHERE trade_date = (SELECT MAX(trade_date) FROM sector_trend_snapshot)
            ORDER BY rank ASC
            LIMIT 6
            """
        )
        risks = self.repo.fetch_all(
            "SELECT * FROM risk_event ORDER BY trade_date DESC, severity DESC, id DESC LIMIT 5"
        )
        signals = self.repo.fetch_all(
            "SELECT * FROM strategy_signal ORDER BY trade_date DESC, score DESC, id DESC LIMIT 8"
        )
        positions = self.repo.fetch_all(
            "SELECT * FROM portfolio_position ORDER BY position_ratio DESC, id DESC LIMIT 10"
        )
        latest_job = self.repo.fetch_one("SELECT * FROM job_execution ORDER BY id DESC LIMIT 1")

        total_market_value = sum(float(item.get("market_value") or 0) for item in positions)
        total_pnl = sum(float(item.get("pnl") or 0) for item in positions)

        return {
            "market": market,
            "sectors": sectors,
            "risks": risks,
            "signals": signals,
            "positions": positions,
            "latest_job": latest_job,
            "summary": {
                "total_market_value": round(total_market_value, 2),
                "total_pnl": round(total_pnl, 2),
                "position_count": len(positions),
                "risk_count": len(risks),
                "signal_count": len(signals),
            },
        }

