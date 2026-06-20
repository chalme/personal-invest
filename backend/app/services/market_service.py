from app.repositories.sqlite_repo import SQLiteRepository


class MarketService:
    def __init__(self, repo: SQLiteRepository | None = None) -> None:
        self.repo = repo or SQLiteRepository()

    def latest_market_trend(self) -> dict | None:
        return self.repo.fetch_one(
            "SELECT * FROM market_trend_snapshot ORDER BY trade_date DESC, id DESC LIMIT 1"
        )

    def market_history(self, limit: int = 60) -> list[dict]:
        safe_limit = max(1, min(int(limit or 60), 240))
        rows = self.repo.fetch_all(
            """
            SELECT
                trade_date,
                market_score,
                trend_state,
                index_trend_score,
                breadth_score,
                volume_score,
                sector_score,
                sentiment_score,
                fund_flow_score,
                summary
            FROM market_trend_snapshot
            ORDER BY trade_date DESC, id DESC
            LIMIT ?
            """,
            (safe_limit,),
        )
        return list(reversed(rows))

    def latest_sectors(self) -> list[dict]:
        return self.repo.fetch_all(
            """
            SELECT * FROM sector_trend_snapshot
            WHERE trade_date = (SELECT MAX(trade_date) FROM sector_trend_snapshot)
            ORDER BY rank ASC, trend_score DESC
            """
        )

    def sector_history(self, limit: int = 20) -> list[dict]:
        safe_limit = max(1, min(int(limit or 20), 120))
        dates = self.repo.fetch_all(
            """
            SELECT DISTINCT trade_date
            FROM sector_trend_snapshot
            ORDER BY trade_date DESC
            LIMIT ?
            """,
            (safe_limit,),
        )
        if not dates:
            return []

        min_date = min(item["trade_date"] for item in dates)
        return self.repo.fetch_all(
            """
            SELECT
                trade_date,
                sector_code,
                sector_name,
                trend_score,
                rank,
                state,
                momentum_20,
                momentum_60,
                volume_change
            FROM sector_trend_snapshot
            WHERE trade_date >= ?
            ORDER BY trade_date ASC, rank ASC
            """,
            (min_date,),
        )

