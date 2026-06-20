from __future__ import annotations

import sqlite3
from datetime import date, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "storage" / "invest.db"
REPORT_DIR = ROOT / "reports" / "daily"


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


def generate_report(conn: sqlite3.Connection) -> Path:
    today = date.today().isoformat()
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / f"{today}.md"

    market = conn.execute("SELECT * FROM market_trend_snapshot ORDER BY trade_date DESC LIMIT 1").fetchone()
    risks = conn.execute("SELECT * FROM risk_event ORDER BY trade_date DESC, severity DESC LIMIT 5").fetchall()
    signals = conn.execute("SELECT * FROM strategy_signal ORDER BY trade_date DESC, score DESC LIMIT 8").fetchall()

    lines = [
        f"# 每日投资报告 - {today}",
        "",
        "## 市场状态",
        f"- 状态：{market['trend_state'] if market else '暂无'}",
        f"- 评分：{market['market_score'] if market else '暂无'}",
        f"- 摘要：{market['summary'] if market else '暂无'}",
        "",
        "## 风险事件",
    ]
    lines.extend([f"- {item['message']}" for item in risks] or ["- 暂无风险事件"])
    lines.extend(["", "## 策略信号"])
    lines.extend([f"- {item['name'] or item['symbol']}：{item['signal_type']}，{item['reason']}" for item in signals] or ["- 暂无策略信号"])
    lines.extend(["", "## 明日关注", "- 优先处理高优先级风险。", "- 观察强势行业是否继续扩散。", "- 个股信号只作为观察，不作为自动交易指令。", ""])

    report_path.write_text("\n".join(lines), encoding="utf-8")
    now = datetime.now().isoformat(timespec="seconds")
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
        (today, f"每日投资报告 - {today}", str(report_path.relative_to(ROOT)), "每日市场、风险、信号摘要", now),
    )
    conn.commit()
    return report_path


def run() -> None:
    if not DB_PATH.exists():
        raise RuntimeError("数据库不存在，请先执行 python scripts/init_db.py")

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        job_id = create_job(conn)
        try:
            update_job(conn, job_id, "RUNNING", 20, "同步行情数据：当前版本使用种子数据占位")
            update_job(conn, job_id, "RUNNING", 45, "计算市场趋势和行业强弱：当前版本读取快照")
            update_job(conn, job_id, "RUNNING", 70, "生成策略信号和风险事件：当前版本读取快照")
            path = generate_report(conn)
            update_job(conn, job_id, "SUCCESS", 100, f"每日报告已生成：{path.relative_to(ROOT)}")
        except Exception as exc:
            update_job(conn, job_id, "FAILED", 100, "每日更新失败", str(exc))
            raise


if __name__ == "__main__":
    run()

