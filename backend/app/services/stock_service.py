from app.repositories.sqlite_repo import SQLiteRepository


class StockService:
    def __init__(self, repo: SQLiteRepository | None = None) -> None:
        self.repo = repo or SQLiteRepository()

    def latest_analysis(self, symbol: str | None = None) -> list[dict]:
        if symbol:
            return self.repo.fetch_all(
                """
                SELECT * FROM stock_analysis_snapshot
                WHERE symbol = ?
                ORDER BY trade_date DESC, id DESC
                LIMIT 30
                """,
                (symbol,),
            )
        return self.repo.fetch_all(
            """
            SELECT * FROM stock_analysis_snapshot
            WHERE trade_date = (SELECT MAX(trade_date) FROM stock_analysis_snapshot)
            ORDER BY total_score DESC, id DESC
            LIMIT 100
            """
        )

