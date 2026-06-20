PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA busy_timeout = 5000;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS watchlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    market TEXT NOT NULL DEFAULT 'A_SHARE',
    group_name TEXT,
    reason TEXT,
    priority INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS portfolio_position (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL DEFAULT 1,
    symbol TEXT NOT NULL,
    name TEXT,
    quantity REAL NOT NULL,
    avg_cost REAL NOT NULL,
    current_price REAL,
    market_value REAL,
    pnl REAL,
    pnl_ratio REAL,
    position_ratio REAL,
    buy_reason TEXT,
    stop_loss_price REAL,
    take_profit_price REAL,
    updated_at TEXT NOT NULL,
    UNIQUE(account_id, symbol)
);

CREATE TABLE IF NOT EXISTS trade_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL DEFAULT 1,
    symbol TEXT NOT NULL,
    trade_date TEXT NOT NULL,
    trade_type TEXT NOT NULL,
    quantity REAL NOT NULL,
    price REAL NOT NULL,
    fee REAL NOT NULL DEFAULT 0,
    reason TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS strategy_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_code TEXT NOT NULL UNIQUE,
    strategy_name TEXT NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1,
    config_json TEXT,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS strategy_signal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_code TEXT NOT NULL,
    symbol TEXT NOT NULL,
    name TEXT,
    trade_date TEXT NOT NULL,
    signal_type TEXT NOT NULL,
    score REAL,
    reason TEXT,
    risk_level TEXT,
    data_version TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(strategy_code, symbol, trade_date)
);

CREATE TABLE IF NOT EXISTS risk_event (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_date TEXT NOT NULL,
    scope TEXT NOT NULL,
    symbol TEXT,
    risk_type TEXT NOT NULL,
    severity INTEGER NOT NULL,
    message TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS market_trend_snapshot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_date TEXT NOT NULL UNIQUE,
    market_score REAL NOT NULL,
    trend_state TEXT NOT NULL,
    index_trend_score REAL,
    breadth_score REAL,
    volume_score REAL,
    sector_score REAL,
    sentiment_score REAL,
    fund_flow_score REAL,
    summary TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sector_trend_snapshot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_date TEXT NOT NULL,
    sector_code TEXT NOT NULL,
    sector_name TEXT NOT NULL,
    trend_score REAL NOT NULL,
    rank INTEGER NOT NULL,
    state TEXT NOT NULL,
    momentum_20 REAL,
    momentum_60 REAL,
    volume_change REAL,
    strength_reason TEXT,
    risk_note TEXT,
    UNIQUE(trade_date, sector_code)
);

CREATE TABLE IF NOT EXISTS stock_analysis_snapshot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_date TEXT NOT NULL,
    symbol TEXT NOT NULL,
    name TEXT NOT NULL,
    total_score REAL NOT NULL,
    state TEXT NOT NULL,
    trend_score REAL,
    fundamental_score REAL,
    valuation_score REAL,
    fund_flow_score REAL,
    sector_score REAL,
    risk_score REAL,
    conclusion TEXT,
    risk_note TEXT,
    data_version TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(trade_date, symbol)
);

CREATE TABLE IF NOT EXISTS report_index (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_type TEXT NOT NULL,
    report_date TEXT NOT NULL,
    title TEXT NOT NULL,
    markdown_path TEXT,
    html_path TEXT,
    summary TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(report_type, report_date)
);

CREATE TABLE IF NOT EXISTS job_execution (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_name TEXT NOT NULL,
    status TEXT NOT NULL,
    progress INTEGER NOT NULL DEFAULT 0,
    started_at TEXT,
    finished_at TEXT,
    message TEXT,
    error TEXT
);

CREATE TABLE IF NOT EXISTS ai_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_type TEXT NOT NULL,
    target TEXT,
    data_version TEXT,
    prompt TEXT,
    result TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS user_setting (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

