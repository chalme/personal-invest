from app.repositories.sqlite_repo import SQLiteRepository


class MarketService:
    def __init__(self, repo: SQLiteRepository | None = None) -> None:
        self.repo = repo or SQLiteRepository()

    def latest_market_trend(self) -> dict | None:
        return self.repo.fetch_one(
            "SELECT * FROM market_trend_snapshot ORDER BY trade_date DESC, id DESC LIMIT 1"
        )

    def latest_sectors(self) -> list[dict]:
        return self.repo.fetch_all(
            """
            SELECT * FROM sector_trend_snapshot
            WHERE trade_date = (SELECT MAX(trade_date) FROM sector_trend_snapshot)
            ORDER BY rank ASC, trend_score DESC
            """
        )

