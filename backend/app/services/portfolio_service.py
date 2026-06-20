from datetime import datetime

from app.repositories.sqlite_repo import SQLiteRepository


class PortfolioService:
    def __init__(self, repo: SQLiteRepository | None = None) -> None:
        self.repo = repo or SQLiteRepository()

    def list_positions(self) -> list[dict]:
        return self.repo.fetch_all(
            "SELECT * FROM portfolio_position ORDER BY position_ratio DESC, market_value DESC"
        )

    def upsert_position(self, payload: dict) -> int:
        quantity = float(payload.get("quantity") or 0)
        avg_cost = float(payload.get("avg_cost") or 0)
        current_price = float(payload.get("current_price") or avg_cost)
        market_value = quantity * current_price
        pnl = quantity * (current_price - avg_cost)
        pnl_ratio = ((current_price / avg_cost) - 1) if avg_cost > 0 else 0
        now = datetime.now().isoformat(timespec="seconds")

        return self.repo.execute(
            """
            INSERT INTO portfolio_position(
                account_id, symbol, name, quantity, avg_cost, current_price,
                market_value, pnl, pnl_ratio, position_ratio, buy_reason,
                stop_loss_price, take_profit_price, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(account_id, symbol) DO UPDATE SET
                name = excluded.name,
                quantity = excluded.quantity,
                avg_cost = excluded.avg_cost,
                current_price = excluded.current_price,
                market_value = excluded.market_value,
                pnl = excluded.pnl,
                pnl_ratio = excluded.pnl_ratio,
                position_ratio = excluded.position_ratio,
                buy_reason = excluded.buy_reason,
                stop_loss_price = excluded.stop_loss_price,
                take_profit_price = excluded.take_profit_price,
                updated_at = excluded.updated_at
            """,
            (
                int(payload.get("account_id") or 1),
                payload["symbol"],
                payload.get("name", payload["symbol"]),
                quantity,
                avg_cost,
                current_price,
                market_value,
                pnl,
                pnl_ratio,
                float(payload.get("position_ratio") or 0),
                payload.get("buy_reason"),
                payload.get("stop_loss_price"),
                payload.get("take_profit_price"),
                now,
            ),
        )

