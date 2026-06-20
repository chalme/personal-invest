from __future__ import annotations

import json
from typing import Any

from worker.storage import connect_db, now_iso, upsert_many


DEFAULT_RISK_SETTINGS: dict[str, Any] = {
    "market_weak_score": 40.0,
    "single_position_limit": 0.20,
    "stock_weak_score": 50.0,
    "enable_stop_loss_check": True,
}


def _decode_setting(value: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def load_risk_settings() -> dict[str, Any]:
    """Load configurable risk thresholds from SQLite.

    The worker intentionally reads settings directly from user_setting instead of
    importing the FastAPI service layer, so the daily job can run independently
    from the web server.
    """
    settings = dict(DEFAULT_RISK_SETTINGS)
    with connect_db() as conn:
        rows = conn.execute(
            "SELECT key, value FROM user_setting WHERE key LIKE 'risk.%'"
        ).fetchall()
    for row in rows:
        key = str(row["key"]).removeprefix("risk.")
        if key in settings:
            settings[key] = _decode_setting(str(row["value"]))
    return settings


def run_risk_check() -> dict[str, Any]:
    now = now_iso()
    risk_settings = load_risk_settings()
    market_weak_score = float(risk_settings["market_weak_score"])
    single_position_limit = float(risk_settings["single_position_limit"])
    stock_weak_score = float(risk_settings["stock_weak_score"])
    enable_stop_loss_check = bool(risk_settings["enable_stop_loss_check"])

    with connect_db() as conn:
        market = conn.execute("SELECT trade_date, market_score, trend_state FROM market_trend_snapshot ORDER BY trade_date DESC LIMIT 1").fetchone()
        positions = conn.execute("SELECT * FROM portfolio_position ORDER BY position_ratio DESC").fetchall()
        analyses = {row["symbol"]: row for row in conn.execute("SELECT * FROM stock_analysis_snapshot WHERE trade_date = (SELECT MAX(trade_date) FROM stock_analysis_snapshot)").fetchall()}
    if not market:
        return {"count": 0}
    trade_date = market["trade_date"]
    values: list[tuple[Any, ...]] = []
    if float(market["market_score"]) < market_weak_score:
        values.append((trade_date, "MARKET", None, "MARKET_WEAK", 3, f"市场状态为{market['trend_state']}，市场分数低于 {market_weak_score:g}，建议降低新开仓频率。", now))
    for pos in positions:
        symbol = pos["symbol"]
        name = pos["name"] or symbol
        ratio = float(pos["position_ratio"] or 0)
        if ratio > single_position_limit:
            values.append((trade_date, "POSITION", symbol, "SINGLE_POSITION_HIGH", 3, f"{name} 单票仓位 {ratio:.1%}，超过 {single_position_limit:.0%} 风控线。", now))
        if enable_stop_loss_check and pos["stop_loss_price"] and pos["current_price"] and float(pos["current_price"]) <= float(pos["stop_loss_price"]):
            values.append((trade_date, "POSITION", symbol, "STOP_LOSS_TOUCHED", 4, f"{name} 已触及止损观察价。", now))
        analysis = analyses.get(symbol)
        if analysis and float(analysis["total_score"]) < stock_weak_score:
            values.append((trade_date, "STOCK", symbol, "SCORE_WEAK", 2, f"{name} 综合评分低于 {stock_weak_score:g}，状态：{analysis['state']}。", now))
    if not values:
        values.append((trade_date, "PORTFOLIO", None, "NO_MAJOR_RISK", 1, "当前没有触发高优先级风险，继续观察数据变化。", now))
    with connect_db() as conn:
        conn.execute("DELETE FROM risk_event WHERE trade_date = ?", (trade_date,))
        count = upsert_many(conn, "INSERT INTO risk_event(trade_date, scope, symbol, risk_type, severity, message, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)", values)
    return {"count": count, "trade_date": trade_date, "settings": risk_settings}
