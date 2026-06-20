from __future__ import annotations

import json
from typing import Any

from worker.storage import connect_db, now_iso, upsert_many


def run_risk_check() -> dict[str, Any]:
    now = now_iso()
    with connect_db() as conn:
        market = conn.execute("SELECT trade_date, market_score, trend_state FROM market_trend_snapshot ORDER BY trade_date DESC LIMIT 1").fetchone()
        positions = conn.execute("SELECT * FROM portfolio_position ORDER BY position_ratio DESC").fetchall()
        analyses = {row["symbol"]: row for row in conn.execute("SELECT * FROM stock_analysis_snapshot WHERE trade_date = (SELECT MAX(trade_date) FROM stock_analysis_snapshot)").fetchall()}
    if not market:
        return {"count": 0}
    trade_date = market["trade_date"]
    values: list[tuple[Any, ...]] = []
    if float(market["market_score"]) < 40:
        values.append((trade_date, "MARKET", None, "MARKET_WEAK", 3, f"市场状态为{market['trend_state']}，建议降低新开仓频率。", now))
    for pos in positions:
        symbol = pos["symbol"]
        name = pos["name"] or symbol
        ratio = float(pos["position_ratio"] or 0)
        if ratio > 0.20:
            values.append((trade_date, "POSITION", symbol, "SINGLE_POSITION_HIGH", 3, f"{name} 单票仓位 {ratio:.1%}，超过 20% 风控线。", now))
        if pos["stop_loss_price"] and pos["current_price"] and float(pos["current_price"]) <= float(pos["stop_loss_price"]):
            values.append((trade_date, "POSITION", symbol, "STOP_LOSS_TOUCHED", 4, f"{name} 已触及止损观察价。", now))
        analysis = analyses.get(symbol)
        if analysis and float(analysis["total_score"]) < 50:
            values.append((trade_date, "STOCK", symbol, "SCORE_WEAK", 2, f"{name} 综合评分低于 50，状态：{analysis['state']}。", now))
    if not values:
        values.append((trade_date, "PORTFOLIO", None, "NO_MAJOR_RISK", 1, "当前没有触发高优先级风险，继续观察数据变化。", now))
    with connect_db() as conn:
        conn.execute("DELETE FROM risk_event WHERE trade_date = ?", (trade_date,))
        count = upsert_many(conn, "INSERT INTO risk_event(trade_date, scope, symbol, risk_type, severity, message, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)", values)
    return {"count": count, "trade_date": trade_date}
