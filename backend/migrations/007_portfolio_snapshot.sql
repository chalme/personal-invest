CREATE TABLE IF NOT EXISTS portfolio_snapshot (
    snapshot_date TEXT NOT NULL,
    account_id INTEGER NOT NULL DEFAULT 1,
    total_market_value REAL NOT NULL DEFAULT 0,
    total_cost REAL NOT NULL DEFAULT 0,
    total_pnl REAL NOT NULL DEFAULT 0,
    total_pnl_ratio REAL NOT NULL DEFAULT 0,
    stock_value REAL NOT NULL DEFAULT 0,
    etf_value REAL NOT NULL DEFAULT 0,
    fund_value REAL NOT NULL DEFAULT 0,
    concentration_hhi REAL NOT NULL DEFAULT 0,
    risk_count INTEGER NOT NULL DEFAULT 0,
    advice_summary TEXT,
    created_at TEXT NOT NULL,
    PRIMARY KEY(snapshot_date, account_id)
);
