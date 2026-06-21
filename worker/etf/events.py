from __future__ import annotations

from typing import Any

from worker.storage import connect_db, now_iso, upsert_many


def generate_etf_deep_events() -> dict[str, Any]:
    now = now_iso()
    with connect_db() as conn:
        rows = conn.execute(
            """
            SELECT l.snapshot_date, l.symbol, l.name,
                   l.liquidity_score, l.liquidity_risk_level, l.liquidity_note,
                   r.risk_return_score, r.risk_level, r.max_drawdown, r.volatility, r.performance_note,
                   t.fit_score, t.tracking_quality_level, t.tracking_error, t.tracking_deviation,
                   t.tracking_note,
                   COALESCE(t.source_mode, r.source_mode, l.source_mode, 'MISSING') AS source_mode,
                   COALESCE(t.data_version, r.data_version, l.data_version) AS data_version
            FROM etf_liquidity_snapshot l
            LEFT JOIN etf_risk_return_snapshot r
              ON r.symbol = l.symbol AND r.snapshot_date = l.snapshot_date
            LEFT JOIN etf_tracking_snapshot t
              ON t.symbol = l.symbol AND t.snapshot_date = l.snapshot_date
            WHERE l.snapshot_date = (SELECT MAX(snapshot_date) FROM etf_liquidity_snapshot)
            """
        ).fetchall()
    events: list[tuple[Any, ...]] = []
    risks: list[tuple[Any, ...]] = []
    for row in rows:
        date = str(row["snapshot_date"])
        symbol = str(row["symbol"])
        name = str(row["name"] or symbol)
        source_mode = str(row["source_mode"] or "MISSING")
        candidates: list[tuple[str, int, str, str]] = []
        if row["liquidity_score"] is not None and float(row["liquidity_score"]) < 45:
            candidates.append(("ETF_LIQUIDITY_WEAK", 2, "ETF 流动性偏弱", f"{name} 流动性评分 {float(row['liquidity_score']):.1f}，{row['liquidity_note']}"))
        if row["risk_return_score"] is not None and float(row["risk_return_score"]) < 40:
            candidates.append(("ETF_RISK_RETURN_WEAK", 2, "ETF 风险收益承压", f"{name} 风险收益评分 {float(row['risk_return_score']):.1f}，{row['performance_note']}"))
        if row["max_drawdown"] is not None and float(row["max_drawdown"]) <= -0.15:
            candidates.append(("ETF_DRAWDOWN_HIGH", 3, "ETF 回撤扩大", f"{name} 最大回撤 {float(row['max_drawdown']):.2%}，需要复核持仓和交易计划。"))
        if row["fit_score"] is not None and float(row["fit_score"]) < 45:
            candidates.append(("ETF_TRACKING_WEAK", 2, "ETF 跟踪质量偏弱", f"{name} 跟踪拟合评分 {float(row['fit_score']):.1f}，{row['tracking_note']}"))
        for event_type, severity, title, message in candidates:
            if source_mode != "REAL":
                severity = min(severity, 2)
                message += f" 当前数据源为 {source_mode}，仅作为低置信度复核提示。"
            events.append((date, symbol, name, event_type, severity, title, message, source_mode, date, row["data_version"], now))
            risks.append((date, "ETF_DEEP", symbol, event_type, severity, message, now))
    with connect_db() as conn:
        if rows:
            date = str(rows[0]["snapshot_date"])
            conn.execute("DELETE FROM risk_event WHERE trade_date = ? AND scope = 'ETF_DEEP'", (date,))
        event_count = upsert_many(conn, _EVENT_SQL, events)
        risk_count = upsert_many(conn, "INSERT INTO risk_event(trade_date, scope, symbol, risk_type, severity, message, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)", risks)
    return {"count": event_count, "risk_count": risk_count, "latest_data_date": str(rows[0]["snapshot_date"]) if rows else None}


_EVENT_SQL = """
INSERT INTO etf_deep_event(event_date, symbol, name, event_type, severity, title, message, source_mode, source_snapshot_date, data_version, created_at)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(event_date, symbol, event_type) DO UPDATE SET
    name=excluded.name,
    severity=excluded.severity,
    title=excluded.title,
    message=excluded.message,
    source_mode=excluded.source_mode,
    source_snapshot_date=excluded.source_snapshot_date,
    data_version=excluded.data_version,
    created_at=excluded.created_at
"""


if __name__ == "__main__":
    print(generate_etf_deep_events())
