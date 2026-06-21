from __future__ import annotations

from datetime import date
from pathlib import Path
from sqlite3 import Row

from worker.storage import REPORT_DIR, connect_db, now_iso


def _stock_focus(stock: Row | None) -> str:
    if not stock:
        return "暂无个股重点"
    return f"{stock['name']}：{stock['conclusion']}"


def _fund_focus(fund: Row | None) -> str:
    if not fund:
        return "暂无基金重点"
    return f"{fund['name']}：{fund['conclusion']}"


def _etf_focus(etf: Row | None) -> str:
    if not etf:
        return "暂无 ETF 重点"
    return f"{etf['name']}：{etf['tracking_quality_level']}"


def _sector_line(sector: Row) -> str:
    return (
        f"- {sector['rank']}. {sector['sector_name']}：{sector['state']}，"
        f"评分 {sector['trend_score']}，{sector['strength_reason']}"
    )


def _stock_line(stock: Row) -> str:
    return (
        f"- {stock['name']}（{stock['symbol']}）：{stock['state']}，"
        f"评分 {stock['total_score']}。{stock['conclusion']}"
    )


def _fund_line(fund: Row) -> str:
    return (
        f"- {fund['name']}（{fund['symbol']}）：{fund['state']}，"
        f"评分 {fund['total_score']}。{fund['conclusion']} 风险：{fund['risk_note']}"
    )


def _etf_line(etf: Row) -> str:
    return (
        f"- {etf['name']}（{etf['symbol']}）：跟踪评分 {etf['fit_score']}，"
        f"状态 {etf['tracking_quality_level']}。{etf['tracking_note']}"
    )


def _signal_line(signal: Row) -> str:
    name = signal["name"] or signal["symbol"]
    return f"- [{signal['asset_type']}] {name}：{signal['signal_type']}，{signal['reason']}"


def build_daily_report() -> Path:
    today = date.today().isoformat()
    with connect_db() as conn:
        market = conn.execute(
            """
            SELECT *
            FROM market_trend_snapshot
            ORDER BY trade_date DESC
            LIMIT 1
            """
        ).fetchone()
        sectors = conn.execute(
            """
            SELECT *
            FROM sector_trend_snapshot
            WHERE trade_date = (SELECT MAX(trade_date) FROM sector_trend_snapshot)
            ORDER BY rank ASC
            LIMIT 5
            """
        ).fetchall()
        stocks = conn.execute(
            """
            SELECT *
            FROM stock_analysis_snapshot
            WHERE trade_date = (SELECT MAX(trade_date) FROM stock_analysis_snapshot)
            ORDER BY total_score DESC
            LIMIT 8
            """
        ).fetchall()
        funds = conn.execute(
            """
            SELECT *
            FROM fund_analysis_snapshot
            WHERE nav_date = (SELECT MAX(nav_date) FROM fund_analysis_snapshot)
            ORDER BY total_score DESC
            LIMIT 8
            """
        ).fetchall()
        etfs = conn.execute(
            """
            SELECT *
            FROM etf_tracking_snapshot
            WHERE snapshot_date = (SELECT MAX(snapshot_date) FROM etf_tracking_snapshot)
            ORDER BY fit_score DESC
            LIMIT 8
            """
        ).fetchall()
        risks = conn.execute(
            """
            SELECT *
            FROM risk_event
            ORDER BY trade_date DESC, severity DESC
            LIMIT 8
            """
        ).fetchall()
        signals = conn.execute(
            """
            SELECT *
            FROM strategy_signal
            ORDER BY trade_date DESC, score DESC
            LIMIT 8
            """
        ).fetchall()

    data_date = market["trade_date"] if market else today
    top_risk = risks[0] if risks else None
    top_stock = stocks[0] if stocks else None
    top_fund = funds[0] if funds else None
    top_etf = etfs[0] if etfs else None
    main_change = (
        top_risk["message"] if top_risk else (market["summary"] if market else "暂无市场简报")
    )
    review_focus = top_risk["message"] if top_risk else "暂无高优先级风险事件，保持观察。"
    tomorrow_focus = "先看市场评分是否继续改善，再处理高等级风险事件。"
    data_boundary = (
        "- 数据边界：本报告基于系统已同步数据生成；"
        "样本、估算或缺失模块只用于低置信解释，不构成确定性投资结论。"
    )

    report_dir = REPORT_DIR / "daily"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"{data_date}.md"
    lines = [
        f"# 每日投资报告 - {data_date}",
        "",
        f"生成时间：{now_iso()}",
        "",
        "## 投资简报",
        f"- 最重要变化：{main_change}",
        f"- 是否需要复核：{review_focus}",
        f"- 明日先看：{tomorrow_focus}",
        f"- 股票重点：{_stock_focus(top_stock)}",
        f"- 基金重点：{_fund_focus(top_fund)}",
        f"- ETF 重点：{_etf_focus(top_etf)}",
        data_boundary,
        "",
        "## 1. 市场状态",
        f"- 状态：{market['trend_state'] if market else '暂无'}",
        f"- 评分：{market['market_score'] if market else '暂无'}",
        f"- 摘要：{market['summary'] if market else '暂无'}",
        "",
        "## 2. 行业强弱",
    ]
    lines.extend([_sector_line(sector) for sector in sectors] or ["- 暂无行业数据"])
    lines.extend(["", "## 3. 个股分析重点"])
    lines.extend([_stock_line(stock) for stock in stocks] or ["- 暂无个股分析"])
    lines.extend(["", "## 4. 基金观察"])
    lines.extend([_fund_line(fund) for fund in funds] or ["- 暂无基金分析"])
    lines.extend(["", "## 5. ETF 深度观察"])
    lines.extend([_etf_line(etf) for etf in etfs] or ["- 暂无 ETF 深度分析"])
    lines.extend(["", "## 6. 风险事件"])
    lines.extend([f"- 级别 {risk['severity']}：{risk['message']}" for risk in risks])
    if not risks:
        lines.append("- 暂无风险事件")
    lines.extend(["", "## 7. 策略信号"])
    lines.extend([_signal_line(signal) for signal in signals] or ["- 暂无策略信号"])
    lines.extend(
        [
            "",
            "## 8. 明日关注",
            "- 先看市场评分是否继续改善。",
            "- 优先处理高等级风险事件。",
            "- 股票、基金和 ETF 信号仅作为观察，不作为自动交易指令。",
            "",
        ]
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")
    with connect_db() as conn:
        conn.execute(
            """
            INSERT INTO report_index(
                report_type,
                report_date,
                title,
                markdown_path,
                summary,
                created_at
            )
            VALUES ('daily', ?, ?, ?, ?, ?)
            ON CONFLICT(report_type, report_date) DO UPDATE SET
                title = excluded.title,
                markdown_path = excluded.markdown_path,
                summary = excluded.summary,
                created_at = excluded.created_at
            """,
            (
                data_date,
                f"每日投资报告 - {data_date}",
                str(report_path.relative_to(REPORT_DIR.parent)),
                "每日市场、行业、个股、基金、风险和信号摘要",
                now_iso(),
            ),
        )
        conn.commit()
    return report_path
