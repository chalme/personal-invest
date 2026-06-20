from __future__ import annotations

from typing import Any

from worker.storage import connect_db, now_iso, upsert_many


def generate_signals() -> dict[str, Any]:
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
        return {"count": 0}
    trade_date = market["trade_date"]
    market_score = float(market["market_score"])
    values: list[tuple[Any, ...]] = []
    for row in stocks:
        score = float(row["total_score"])
        if score >= 80 and market_score >= 45:
            signal_type = "高质量观察"
            risk_level = "LOW"
            reason = f"综合评分 {score:.0f}，市场评分 {market_score:.0f}，进入重点观察。"
        elif score >= 65 and market_score >= 55:
            signal_type = "趋势观察"
            risk_level = "MEDIUM"
            reason = f"趋势和市场环境配合，综合评分 {score:.0f}。"
        elif score < 45:
            signal_type = "风险上升"
            risk_level = "HIGH"
            reason = f"综合评分降至 {score:.0f}，需降低关注优先级。"
        else:
            continue
        values.append(("personal_watch_v1", row["symbol"], row["name"], trade_date, signal_type, score, reason, risk_level, row["data_version"], now))
    with connect_db() as conn:
        count = upsert_many(conn, """
            INSERT INTO strategy_signal(
                strategy_code, symbol, name, trade_date, signal_type, score, reason, risk_level, data_version, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(strategy_code, symbol, trade_date) DO UPDATE SET
                name = excluded.name,
                signal_type = excluded.signal_type,
                score = excluded.score,
                reason = excluded.reason,
                risk_level = excluded.risk_level,
                data_version = excluded.data_version,
                created_at = excluded.created_at
            """, values)
    return {"count": count, "trade_date": trade_date}
