from __future__ import annotations

from typing import Any

from worker.storage import connect_db, now_iso, upsert_many


def _severity(source_mode: str, base: int) -> int:
    return min(base, 2) if source_mode != "REAL" else base


def generate_financial_events() -> dict[str, Any]:
    now = now_iso()
    with connect_db() as conn:
        rows = conn.execute(
            """
            SELECT q.quality_date, q.symbol, q.name, q.total_score, q.quality_state,
                   q.source_mode, q.data_version, q.risk_note,
                   m.debt_ratio, m.operating_cash_flow_ratio,
                   v.valuation_score, v.valuation_state
            FROM stock_quality_snapshot q
            LEFT JOIN financial_metric_snapshot m
              ON m.symbol = q.symbol AND m.metric_date = q.quality_date
            LEFT JOIN valuation_snapshot v
              ON v.symbol = q.symbol AND v.valuation_date = q.quality_date
            WHERE q.quality_date = (SELECT MAX(quality_date) FROM stock_quality_snapshot)
            """
        ).fetchall()
    events: list[tuple[Any, ...]] = []
    risks: list[tuple[Any, ...]] = []
    for row in rows:
        source_mode = str(row["source_mode"] or "MISSING")
        date = str(row["quality_date"])
        symbol = str(row["symbol"])
        name = str(row["name"] or symbol)
        data_version = str(row["data_version"] or "")
        candidates: list[tuple[str, int, str, str]] = []
        if float(row["total_score"] or 0) < 45:
            candidates.append(("FINANCIAL_QUALITY_WEAK", 3, "公司质量承压", f"{name} 公司质量评分 {float(row['total_score'] or 0):.1f}，状态：{row['quality_state']}。"))
        if row["debt_ratio"] is not None and float(row["debt_ratio"]) > 0.75:
            candidates.append(("FINANCIAL_DEBT_HIGH", 3, "负债率偏高", f"{name} 资产负债率 {float(row['debt_ratio']):.1%}，需要复核偿债和现金流风险。"))
        if row["operating_cash_flow_ratio"] is not None and float(row["operating_cash_flow_ratio"]) < 0.7:
            candidates.append(("FINANCIAL_CASHFLOW_WEAK", 3, "现金流质量偏弱", f"{name} 经营现金流 / 净利润为 {float(row['operating_cash_flow_ratio']):.2f}，利润含金量需要复核。"))
        if row["valuation_score"] is not None and float(row["valuation_score"]) < 30:
            candidates.append(("FINANCIAL_VALUATION_RICH", 2, "估值偏贵", f"{name} 估值评分 {float(row['valuation_score']):.1f}，状态：{row['valuation_state']}。"))
        for event_type, base_severity, title, message in candidates:
            severity = _severity(source_mode, base_severity)
            if source_mode != "REAL":
                message = message + f" 当前数据源为 {source_mode}，仅作为低置信度复核提示。"
            events.append((date, symbol, name, event_type, severity, title, message, source_mode, date, data_version, now))
            risks.append((date, "FINANCIAL", symbol, event_type, severity, message, now))
    with connect_db() as conn:
        if rows:
            date = str(rows[0]["quality_date"])
            conn.execute("DELETE FROM risk_event WHERE trade_date = ? AND scope = 'FINANCIAL'", (date,))
        event_count = upsert_many(conn, """
            INSERT INTO financial_event(event_date, symbol, name, event_type, severity, title, message, source_mode, source_snapshot_date, data_version, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(event_date, symbol, event_type) DO UPDATE SET
                name=excluded.name, severity=excluded.severity, title=excluded.title,
                message=excluded.message, source_mode=excluded.source_mode,
                source_snapshot_date=excluded.source_snapshot_date,
                data_version=excluded.data_version, created_at=excluded.created_at
        """, events)
        risk_count = upsert_many(conn, "INSERT INTO risk_event(trade_date, scope, symbol, risk_type, severity, message, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)", risks)
    return {"count": event_count, "risk_count": risk_count, "latest_data_date": str(rows[0]["quality_date"]) if rows else None}


if __name__ == "__main__":
    print(generate_financial_events())
