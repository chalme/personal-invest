from __future__ import annotations

import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

from migrate_db import run_migrations


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "storage" / "invest.db"
MIGRATION = ROOT / "backend" / "migrations" / "001_init.sql"


def execute_sql_file(conn: sqlite3.Connection, path: Path) -> None:
    conn.executescript(path.read_text(encoding="utf-8"))




def infer_asset_type(symbol: str, market: str | None = None, explicit: str | None = None) -> str:
    if explicit and explicit.upper() in {"STOCK", "ETF", "FUND"}:
        return explicit.upper()
    if (market or "").upper() in {"FUND", "MUTUAL_FUND"}:
        return "FUND"
    code = symbol.upper().split(".")[0]
    suffix = symbol.upper().split(".")[-1] if "." in symbol else ""
    if suffix in {"OF", "FUND"}:
        return "FUND"
    if code.startswith(("15", "16", "50", "51", "52", "56", "58")):
        return "ETF"
    return "STOCK"


def table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}


def ensure_asset_type_columns(conn: sqlite3.Connection) -> None:
    if "asset_type" not in table_columns(conn, "watchlist"):
        conn.execute("ALTER TABLE watchlist ADD COLUMN asset_type TEXT NOT NULL DEFAULT 'STOCK'")
    if "asset_type" not in table_columns(conn, "portfolio_position"):
        conn.execute("ALTER TABLE portfolio_position ADD COLUMN asset_type TEXT NOT NULL DEFAULT 'STOCK'")
    if "asset_type" not in table_columns(conn, "strategy_signal"):
        conn.execute("ALTER TABLE strategy_signal ADD COLUMN asset_type TEXT NOT NULL DEFAULT 'STOCK'")
    for row in conn.execute("SELECT id, symbol, market FROM watchlist").fetchall():
        conn.execute("UPDATE watchlist SET asset_type = ? WHERE id = ?", (infer_asset_type(row[1], row[2]), row[0]))
    for row in conn.execute("SELECT id, symbol FROM portfolio_position").fetchall():
        conn.execute("UPDATE portfolio_position SET asset_type = ? WHERE id = ?", (infer_asset_type(row[1]), row[0]))
    for row in conn.execute("SELECT id, symbol FROM strategy_signal").fetchall():
        conn.execute("UPDATE strategy_signal SET asset_type = ? WHERE id = ?", (infer_asset_type(row[1]), row[0]))


def ensure_advice_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS investment_advice (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL DEFAULT 1,
            symbol TEXT NOT NULL,
            name TEXT,
            asset_type TEXT NOT NULL DEFAULT 'STOCK',
            holding_status TEXT NOT NULL DEFAULT 'WATCHING',
            advice_date TEXT NOT NULL,
            advice_level TEXT NOT NULL,
            one_liner TEXT NOT NULL,
            trigger_reason TEXT NOT NULL,
            key_metrics TEXT,
            risk_note TEXT,
            review_action TEXT NOT NULL,
            confidence REAL NOT NULL DEFAULT 0.5,
            data_version TEXT,
            created_at TEXT NOT NULL,
            UNIQUE(account_id, symbol, advice_date)
        )
        """
    )

def seed(conn: sqlite3.Connection) -> None:
    current = date.today()
    while current.weekday() >= 5:
        current -= timedelta(days=1)
    today = current.isoformat()
    now = datetime.now().isoformat(timespec="seconds")

    conn.execute(
        """
        INSERT OR IGNORE INTO market_trend_snapshot(
            trade_date, market_score, trend_state, index_trend_score, breadth_score,
            volume_score, sector_score, sentiment_score, fund_flow_score, summary, created_at
        ) VALUES (?, 62, '震荡偏强', 65, 58, 61, 66, 55, 50, ?, ?)
        """,
        (today, "市场处于震荡偏强状态，适合观察结构性机会，但仍需要控制仓位。", now),
    )

    sectors = [
        ("TECH", "科技", 78, 1, "强势", 0.08, 0.16, 0.22, "趋势和成交额同步改善", "短期涨幅偏大"),
        ("CONSUME", "消费", 68, 2, "修复", 0.04, 0.09, 0.08, "估值修复，龙头稳定", "需求恢复仍需验证"),
        ("BANK", "银行", 60, 3, "稳健", 0.02, 0.06, 0.03, "高股息防御属性", "弹性不足"),
        ("NEW_ENERGY", "新能源", 47, 4, "分化", -0.01, -0.04, -0.05, "部分龙头企稳", "行业仍在出清"),
    ]
    conn.executemany(
        """
        INSERT OR IGNORE INTO sector_trend_snapshot(
            trade_date, sector_code, sector_name, trend_score, rank, state,
            momentum_20, momentum_60, volume_change, strength_reason, risk_note
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [(today, *item) for item in sectors],
    )

    stocks = [
        (today, "600519.SH", "贵州茅台", 82, "高质量观察", 74, 94, 62, 66, 75, 20, "公司质量强，适合长期观察。", "估值不低，需注意消费需求变化。", "seed", now),
        (today, "510300.SH", "沪深300ETF", 70, "趋势观察", 72, 60, 70, 55, 68, 25, "适合观察市场 Beta 修复。", "市场回落时跟随下跌。", "seed", now),
        (today, "000001.SZ", "平安银行", 58, "持有观察", 54, 63, 66, 50, 59, 36, "估值较低，趋势仍需确认。", "银行地产链风险仍需关注。", "seed", now),
    ]
    conn.executemany(
        """
        INSERT OR IGNORE INTO stock_analysis_snapshot(
            trade_date, symbol, name, total_score, state, trend_score, fundamental_score,
            valuation_score, fund_flow_score, sector_score, risk_score, conclusion,
            risk_note, data_version, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        stocks,
    )

    watchlist = [
        ("600519.SH", "贵州茅台", "STOCK", "A_SHARE", "消费", "高质量龙头，长期观察", 9, "ACTIVE", now, now),
        ("510300.SH", "沪深300ETF", "ETF", "A_SHARE", "ETF", "观察市场 Beta", 8, "ACTIVE", now, now),
        ("000001.SZ", "平安银行", "STOCK", "A_SHARE", "银行", "低估值银行样本", 6, "ACTIVE", now, now),
    ]
    conn.executemany(
        """
        INSERT OR IGNORE INTO watchlist(symbol, name, asset_type, market, group_name, reason, priority, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        watchlist,
    )

    positions = [
        (1, "510300.SH", "沪深300ETF", "ETF", 1000, 3.80, 3.95, 3950, 150, 0.0395, 0.35, "核心宽基观察仓", 3.55, 4.3, now),
        (1, "000001.SZ", "平安银行", "STOCK", 500, 10.20, 10.55, 5275, 175, 0.0343, 0.22, "低估值修复观察", 9.60, 12.0, now),
    ]
    conn.executemany(
        """
        INSERT OR IGNORE INTO portfolio_position(
            account_id, symbol, name, asset_type, quantity, avg_cost, current_price, market_value,
            pnl, pnl_ratio, position_ratio, buy_reason, stop_loss_price, take_profit_price, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        positions,
    )

    conn.execute(
        """
        INSERT OR IGNORE INTO strategy_config(strategy_code, strategy_name, enabled, config_json, updated_at)
        VALUES (?, ?, 1, ?, ?)
        """,
        (
            "personal_watch_v1",
            "个人观察策略 V1",
            '{"high_quality_score": 80, "high_quality_market_score": 45, "trend_watch_score": 65, "trend_watch_market_score": 55, "risk_score": 45}',
            now,
        ),
    )

    signals = [
        ("market_trend_v1", "510300.SH", "沪深300ETF", "ETF", today, "进入观察", 72, "市场震荡偏强，宽基趋势改善。", "MEDIUM", "seed", now),
        ("quality_watch_v1", "600519.SH", "贵州茅台", "STOCK", today, "高质量观察", 82, "基本面质量高，但估值需要等待更好位置。", "LOW", "seed", now),
    ]
    conn.executemany(
        """
        INSERT OR IGNORE INTO strategy_signal(
            strategy_code, symbol, name, asset_type, trade_date, signal_type, score, reason, risk_level, data_version, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        signals,
    )

    risks = [
        (today, "PORTFOLIO", None, "POSITION_CONCENTRATION", 2, "当前仓位以宽基和银行为主，行业分散度仍需继续提升。", now),
        (today, "STOCK", "000001.SZ", "TREND_CONFIRMATION", 1, "趋势尚未完全走强，继续观察量能变化。", now),
    ]
    conn.executemany(
        """
        INSERT OR IGNORE INTO risk_event(trade_date, scope, symbol, risk_type, severity, message, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        risks,
    )


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        execute_sql_file(conn, MIGRATION)
        ensure_asset_type_columns(conn)
        ensure_advice_table(conn)
        seed(conn)
        conn.commit()
    run_migrations(DB_PATH)
    print(f"initialized: {DB_PATH}")


if __name__ == "__main__":
    main()

