from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from app.core.asset_type import infer_asset_type
from app.repositories.sqlite_repo import SQLiteRepository


class PortfolioService:
    def __init__(self, repo: SQLiteRepository | None = None) -> None:
        self.repo = repo or SQLiteRepository()

    def list_positions(self) -> list[dict]:
        return self.repo.fetch_all(
            "SELECT * FROM portfolio_position ORDER BY position_ratio DESC, market_value DESC"
        )

    def portfolio_overview(self) -> dict:
        positions = self.list_positions()
        latest_analysis_date = self.repo.fetch_one("SELECT MAX(trade_date) AS trade_date FROM stock_analysis_snapshot")
        latest_risk_date = self.repo.fetch_one("SELECT MAX(trade_date) AS trade_date FROM risk_event")
        analysis_date = latest_analysis_date.get("trade_date") if latest_analysis_date else None
        risk_date = latest_risk_date.get("trade_date") if latest_risk_date else None

        analyses = self.repo.fetch_all(
            "SELECT * FROM stock_analysis_snapshot WHERE trade_date = ?",
            (analysis_date,),
        ) if analysis_date else []
        analysis_by_symbol = {item["symbol"]: item for item in analyses}

        risks = self.repo.fetch_all(
            "SELECT * FROM risk_event WHERE trade_date = ? ORDER BY severity DESC, id DESC",
            (risk_date,),
        ) if risk_date else []
        risks_by_symbol: dict[str, list[dict]] = defaultdict(list)
        portfolio_risks: list[dict] = []
        for risk in risks:
            symbol = risk.get("symbol")
            if symbol:
                risks_by_symbol[symbol].append(risk)
            else:
                portfolio_risks.append(risk)

        total_market_value = sum(float(item.get("market_value") or 0) for item in positions)
        total_cost = sum(float(item.get("quantity") or 0) * float(item.get("avg_cost") or 0) for item in positions)
        total_pnl = sum(float(item.get("pnl") or 0) for item in positions)
        total_pnl_ratio = (total_pnl / total_cost) if total_cost > 0 else 0

        enriched_positions = []
        concentration = 0.0
        for position in positions:
            symbol = position["symbol"]
            market_value = float(position.get("market_value") or 0)
            computed_ratio = (market_value / total_market_value) if total_market_value > 0 else 0
            position_ratio = float(position.get("position_ratio") or computed_ratio)
            concentration += position_ratio * position_ratio
            position_risks = risks_by_symbol.get(symbol, [])
            enriched_positions.append({
                **position,
                "computed_position_ratio": round(computed_ratio, 4),
                "analysis": analysis_by_symbol.get(symbol),
                "risks": position_risks,
                "risk_count": len(position_risks),
                "max_risk_severity": max((int(item.get("severity") or 0) for item in position_risks), default=0),
            })

        return {
            "summary": {
                "total_market_value": round(total_market_value, 2),
                "total_cost": round(total_cost, 2),
                "total_pnl": round(total_pnl, 2),
                "total_pnl_ratio": round(total_pnl_ratio, 4),
                "position_count": len(positions),
                "portfolio_risk_count": len(portfolio_risks),
                "symbol_risk_count": sum(len(items) for items in risks_by_symbol.values()),
                "concentration_hhi": round(concentration, 4),
                "analysis_date": analysis_date,
                "risk_date": risk_date,
            },
            "positions": enriched_positions,
            "portfolio_risks": portfolio_risks,
        }

    def upsert_position(self, payload: dict) -> int:
        quantity = float(payload.get("quantity") or 0)
        avg_cost = float(payload.get("avg_cost") or 0)
        current_price = float(payload.get("current_price") or avg_cost)
        market_value = quantity * current_price
        pnl = quantity * (current_price - avg_cost)
        pnl_ratio = ((current_price / avg_cost) - 1) if avg_cost > 0 else 0
        asset_type = infer_asset_type(payload["symbol"], explicit=payload.get("asset_type"))
        now = datetime.now().isoformat(timespec="seconds")

        return self.repo.execute(
            """
            INSERT INTO portfolio_position(
                account_id, symbol, name, asset_type, quantity, avg_cost, current_price,
                market_value, pnl, pnl_ratio, position_ratio, buy_reason,
                stop_loss_price, take_profit_price, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(account_id, symbol) DO UPDATE SET
                name = excluded.name,
                asset_type = excluded.asset_type,
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
                asset_type,
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

    def remove_position(self, symbol: str, account_id: int = 1) -> None:
        self.repo.execute(
            "DELETE FROM portfolio_position WHERE account_id = ? AND symbol = ?",
            (account_id, symbol),
        )

