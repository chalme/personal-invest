from __future__ import annotations

from typing import Any

from worker.storage import connect_db, now_iso, upsert_many


def generate_fund_deep_events() -> dict[str, Any]:
    now = now_iso()
    with connect_db() as conn:
        rows = conn.execute(
            """
            SELECT r.snapshot_date, r.symbol, r.name, r.return_3m, r.max_drawdown,
                   r.volatility, r.risk_return_score, r.holding_experience,
                   r.source_mode, r.data_version,
                   b.excess_return_3m, b.benchmark_score,
                   p.peer_score
            FROM fund_risk_return_snapshot r
            LEFT JOIN fund_benchmark_snapshot b
              ON b.symbol = r.symbol AND b.snapshot_date = r.snapshot_date
            LEFT JOIN fund_peer_rank_snapshot p
              ON p.symbol = r.symbol AND p.snapshot_date = r.snapshot_date
            WHERE r.snapshot_date = (SELECT MAX(snapshot_date) FROM fund_risk_return_snapshot)
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
        if row["risk_return_score"] is not None and float(row["risk_return_score"]) < 40:
            candidates.append(("FUND_DEEP_RISK_RETURN_WEAK", 3, "风险收益承压", f"{name} 风险收益评分 {float(row['risk_return_score']):.1f}，持有体验：{row['holding_experience']}。"))
        if row["max_drawdown"] is not None and float(row["max_drawdown"]) <= -0.15:
            candidates.append(("FUND_DEEP_DRAWDOWN_HIGH", 3, "基金回撤扩大", f"{name} 最大回撤 {float(row['max_drawdown']):.2%}，需要复核持有体验和仓位。"))
        if row["excess_return_3m"] is not None and float(row["excess_return_3m"]) < -0.05:
            candidates.append(("FUND_DEEP_BENCHMARK_LAG", 2, "跑输基准", f"{name} 近三月相对基准收益 {float(row['excess_return_3m']):.2%}。"))
        if row["peer_score"] is not None and float(row["peer_score"]) < 35:
            candidates.append(("FUND_DEEP_PEER_WEAK", 2, "同类位置偏弱", f"{name} 同类评分 {float(row['peer_score']):.1f}，需要复核替代基金。"))
        for event_type, severity, title, message in candidates:
            if source_mode != "REAL":
                severity = min(severity, 2)
                message += f" 当前数据源为 {source_mode}，仅作为低置信度复核提示。"
            events.append((date, symbol, name, event_type, severity, title, message, source_mode, date, row["data_version"], now))
            risks.append((date, "FUND_DEEP", symbol, event_type, severity, message, now))
    with connect_db() as conn:
        if rows:
            date = str(rows[0]["snapshot_date"])
            conn.execute("DELETE FROM risk_event WHERE trade_date = ? AND scope = 'FUND_DEEP'", (date,))
        event_count = upsert_many(conn, """
            INSERT INTO fund_deep_event(event_date, symbol, name, event_type, severity, title, message, source_mode, source_snapshot_date, data_version, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(event_date, symbol, event_type) DO UPDATE SET
                name=excluded.name, severity=excluded.severity, title=excluded.title,
                message=excluded.message, source_mode=excluded.source_mode,
                source_snapshot_date=excluded.source_snapshot_date, data_version=excluded.data_version,
                created_at=excluded.created_at
        """, events)
        risk_count = upsert_many(conn, "INSERT INTO risk_event(trade_date, scope, symbol, risk_type, severity, message, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)", risks)
    return {"count": event_count, "risk_count": risk_count, "latest_data_date": str(rows[0]["snapshot_date"]) if rows else None}


if __name__ == "__main__":
    print(generate_fund_deep_events())
