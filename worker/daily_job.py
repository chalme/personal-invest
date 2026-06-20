from __future__ import annotations

import sqlite3
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from worker.factor.fund_analysis import calculate_fund_analysis
from worker.factor.market_trend import calculate_market_trend, calculate_sector_trend
from worker.factor.stock_analysis import calculate_stock_analysis
from worker.ingest.market_data import sync_fund_data, sync_market_data
from worker.report.report_builder import build_daily_report
from worker.risk.risk_engine import run_risk_check
from worker.storage import DB_PATH, connect_db
from worker.strategy.signal_engine import generate_signals


def update_job(conn: sqlite3.Connection, job_id: int, status: str, progress: int, message: str, error: str | None = None) -> None:
    conn.execute(
        """
        UPDATE job_execution
        SET status = ?, progress = ?, message = ?, error = ?, finished_at = CASE WHEN ? IN ('SUCCESS', 'FAILED') THEN ? ELSE finished_at END
        WHERE id = ?
        """,
        (status, progress, message, error, status, datetime.now().isoformat(timespec="seconds"), job_id),
    )
    conn.commit()


def create_job(conn: sqlite3.Connection) -> int:
    now = datetime.now().isoformat(timespec="seconds")
    cursor = conn.execute(
        """
        INSERT INTO job_execution(job_name, status, progress, started_at, message)
        VALUES ('daily_update', 'RUNNING', 0, ?, '开始执行每日更新')
        """,
        (now,),
    )
    conn.commit()
    return int(cursor.lastrowid)


def run(job_id: int | None = None) -> None:
    if not DB_PATH.exists():
        raise RuntimeError("数据库不存在，请先执行 python scripts/init_db.py")
    with connect_db() as conn:
        if job_id is None:
            job_id = create_job(conn)
        else:
            update_job(conn, job_id, "RUNNING", 0, "开始执行每日更新")
        try:
            update_job(conn, job_id, "RUNNING", 10, "同步行情数据")
            market_sync = sync_market_data()

            update_job(conn, job_id, "RUNNING", 20, "同步基金净值数据")
            fund_sync = sync_fund_data()

            update_job(conn, job_id, "RUNNING", 30, "计算市场趋势")
            market = calculate_market_trend()

            update_job(conn, job_id, "RUNNING", 45, "计算行业强弱")
            sectors = calculate_sector_trend()

            update_job(conn, job_id, "RUNNING", 60, "计算个股公司分析")
            stocks = calculate_stock_analysis()

            update_job(conn, job_id, "RUNNING", 70, "计算基金分析")
            funds = calculate_fund_analysis()

            update_job(conn, job_id, "RUNNING", 78, "生成策略信号")
            signals = generate_signals()

            update_job(conn, job_id, "RUNNING", 85, "执行持仓风控")
            risks = run_risk_check()

            update_job(conn, job_id, "RUNNING", 95, "生成每日投资报告")
            report_path = build_daily_report()

            update_job(
                conn,
                job_id,
                "SUCCESS",
                100,
                (
                    f"完成：行情 {market_sync['rows']} 行，基金净值 {fund_sync['rows']} 行，市场 {market['trend_state']}，"
                    f"行业 {sectors.get('count', 0)} 个，个股 {stocks.get('count', 0)} 个，"
                    f"基金 {funds.get('count', 0)} 个，信号 {signals.get('count', 0)} 条，"
                    f"风险 {risks.get('count', 0)} 条，"
                    f"报告 {report_path}"
                ),
            )
        except Exception as exc:
            update_job(conn, job_id, "FAILED", 100, "每日更新失败", str(exc))
            raise


if __name__ == "__main__":
    run()
