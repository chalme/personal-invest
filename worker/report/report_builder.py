from __future__ import annotations

from datetime import date
from pathlib import Path

from worker.storage import REPORT_DIR, connect_db, now_iso


def build_daily_report() -> Path:
    today = date.today().isoformat()
    with connect_db() as conn:
        market = conn.execute("SELECT * FROM market_trend_snapshot ORDER BY trade_date DESC LIMIT 1").fetchone()
        sectors = conn.execute("SELECT * FROM sector_trend_snapshot WHERE trade_date = (SELECT MAX(trade_date) FROM sector_trend_snapshot) ORDER BY rank ASC LIMIT 5").fetchall()
        stocks = conn.execute("SELECT * FROM stock_analysis_snapshot WHERE trade_date = (SELECT MAX(trade_date) FROM stock_analysis_snapshot) ORDER BY total_score DESC LIMIT 8").fetchall()
        risks = conn.execute("SELECT * FROM risk_event ORDER BY trade_date DESC, severity DESC LIMIT 8").fetchall()
        signals = conn.execute("SELECT * FROM strategy_signal ORDER BY trade_date DESC, score DESC LIMIT 8").fetchall()
    data_date = market["trade_date"] if market else today
    report_dir = REPORT_DIR / "daily"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"{data_date}.md"
    lines = [
        f"# 每日投资报告 - {data_date}",
        "",
        f"生成时间：{now_iso()}",
        "",
        "## 1. 市场状态",
        f"- 状态：{market['trend_state'] if market else '暂无'}",
        f"- 评分：{market['market_score'] if market else '暂无'}",
        f"- 摘要：{market['summary'] if market else '暂无'}",
        "",
        "## 2. 行业强弱",
    ]
    lines.extend([f"- {s['rank']}. {s['sector_name']}：{s['state']}，评分 {s['trend_score']}，{s['strength_reason']}" for s in sectors] or ["- 暂无行业数据"])
    lines.extend(["", "## 3. 个股分析重点"])
    lines.extend([f"- {s['name']}（{s['symbol']}）：{s['state']}，评分 {s['total_score']}。{s['conclusion']}" for s in stocks] or ["- 暂无个股分析"])
    lines.extend(["", "## 4. 风险事件"])
    lines.extend([f"- 级别 {r['severity']}：{r['message']}" for r in risks] or ["- 暂无风险事件"])
    lines.extend(["", "## 5. 策略信号"])
    lines.extend([f"- {s['name'] or s['symbol']}：{s['signal_type']}，{s['reason']}" for s in signals] or ["- 暂无策略信号"])
    lines.extend(["", "## 6. 明日关注", "- 先看市场评分是否继续改善。", "- 优先处理高等级风险事件。", "- 个股信号仅作为观察，不作为自动交易指令。", ""])
    report_path.write_text("\n".join(lines), encoding="utf-8")
    with connect_db() as conn:
        conn.execute(
            """
            INSERT INTO report_index(report_type, report_date, title, markdown_path, summary, created_at)
            VALUES ('daily', ?, ?, ?, ?, ?)
            ON CONFLICT(report_type, report_date) DO UPDATE SET
                title = excluded.title,
                markdown_path = excluded.markdown_path,
                summary = excluded.summary,
                created_at = excluded.created_at
            """,
            (data_date, f"每日投资报告 - {data_date}", str(report_path.relative_to(REPORT_DIR.parent)), "每日市场、行业、个股、风险和信号摘要", now_iso()),
        )
        conn.commit()
    return report_path
