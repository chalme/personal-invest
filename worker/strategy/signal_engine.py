from __future__ import annotations

import json
from typing import Any

from worker.storage import connect_db, now_iso, upsert_many


DEFAULT_STRATEGY_PARAMS: dict[str, float] = {
    "high_quality_score": 80,
    "high_quality_market_score": 45,
    "trend_watch_score": 65,
    "trend_watch_market_score": 55,
    "risk_score": 45,
}


def infer_asset_type(symbol: str) -> str:
    code = symbol.upper().split(".")[0]
    suffix = symbol.upper().split(".")[-1] if "." in symbol else ""
    if suffix in {"OF", "FUND"}:
        return "FUND"
    if code.startswith(("15", "16", "50", "51", "52", "56", "58")):
        return "ETF"
    return "STOCK"


def load_strategy_config(strategy_code: str = "personal_watch_v1") -> dict[str, Any]:
    params = dict(DEFAULT_STRATEGY_PARAMS)
    enabled = True
    strategy_name = "个人观察策略 V1"
    with connect_db() as conn:
        row = conn.execute(
            """
            SELECT strategy_name, enabled, config_json
            FROM strategy_config
            WHERE strategy_code = ?
            """,
            (strategy_code,),
        ).fetchone()
    if not row:
        return {"strategy_code": strategy_code, "strategy_name": strategy_name, "enabled": enabled, "params": params}
    enabled = bool(row["enabled"])
    strategy_name = row["strategy_name"] or strategy_name
    try:
        raw_params = json.loads(row["config_json"] or "{}")
    except json.JSONDecodeError:
        raw_params = {}
    for key, default in DEFAULT_STRATEGY_PARAMS.items():
        try:
            value = float(raw_params.get(key, default))
        except (TypeError, ValueError):
            value = default
        params[key] = min(100.0, max(0.0, value))
    return {"strategy_code": strategy_code, "strategy_name": strategy_name, "enabled": enabled, "params": params}


def generate_signals() -> dict[str, Any]:
    config = load_strategy_config()
    strategy_code = config["strategy_code"]
    params = config["params"]
    now = now_iso()
    with connect_db() as conn:
        market = conn.execute("SELECT * FROM market_trend_snapshot ORDER BY trade_date DESC LIMIT 1").fetchone()
        stocks = conn.execute(
            """
            SELECT * FROM stock_analysis_snapshot
            WHERE trade_date = (SELECT MAX(trade_date) FROM stock_analysis_snapshot)
            ORDER BY total_score DESC
            """
        ).fetchall()
    if not market:
        return {"count": 0, "strategy_code": strategy_code, "enabled": config["enabled"]}
    trade_date = market["trade_date"]
    if not config["enabled"]:
        return {"count": 0, "trade_date": trade_date, "strategy_code": strategy_code, "enabled": False}

    market_score = float(market["market_score"])
    values: list[tuple[Any, ...]] = []
    for row in stocks:
        score = float(row["total_score"])
        if score >= params["high_quality_score"] and market_score >= params["high_quality_market_score"]:
            signal_type = "高质量观察"
            risk_level = "LOW"
            reason = f"综合评分 {score:.0f}，市场评分 {market_score:.0f}，达到高质量观察阈值。"
        elif score >= params["trend_watch_score"] and market_score >= params["trend_watch_market_score"]:
            signal_type = "趋势观察"
            risk_level = "MEDIUM"
            reason = f"综合评分 {score:.0f}，市场评分 {market_score:.0f}，达到趋势观察阈值。"
        elif score < params["risk_score"]:
            signal_type = "风险上升"
            risk_level = "HIGH"
            reason = f"综合评分降至 {score:.0f}，低于风险阈值 {params['risk_score']:.0f}。"
        else:
            continue
        values.append((strategy_code, row["symbol"], row["name"], infer_asset_type(row["symbol"]), trade_date, signal_type, score, reason, risk_level, row["data_version"], now))
    with connect_db() as conn:
        count = upsert_many(conn, """
            INSERT INTO strategy_signal(
                strategy_code, symbol, name, asset_type, trade_date, signal_type, score, reason, risk_level, data_version, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(strategy_code, symbol, trade_date) DO UPDATE SET
                name = excluded.name,
                asset_type = excluded.asset_type,
                signal_type = excluded.signal_type,
                score = excluded.score,
                reason = excluded.reason,
                risk_level = excluded.risk_level,
                data_version = excluded.data_version,
                created_at = excluded.created_at
            """, values)
    return {"count": count, "trade_date": trade_date, "strategy_code": strategy_code, "enabled": True}
