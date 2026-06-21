CREATE TABLE IF NOT EXISTS fund_profile (
    symbol TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    fund_type TEXT,
    risk_level TEXT,
    manager_name TEXT,
    company_name TEXT,
    benchmark TEXT,
    fee_note TEXT,
    source TEXT,
    source_mode TEXT NOT NULL DEFAULT 'SAMPLE',
    data_date TEXT NOT NULL,
    data_version TEXT,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS fund_manager_profile (
    manager_name TEXT PRIMARY KEY,
    company_name TEXT,
    tenure_years REAL,
    style_note TEXT,
    source TEXT,
    source_mode TEXT NOT NULL DEFAULT 'SAMPLE',
    data_date TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS fund_company_profile (
    company_name TEXT PRIMARY KEY,
    scale_note TEXT,
    risk_control_note TEXT,
    source TEXT,
    source_mode TEXT NOT NULL DEFAULT 'SAMPLE',
    data_date TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS fund_risk_return_snapshot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_date TEXT NOT NULL,
    symbol TEXT NOT NULL,
    name TEXT NOT NULL,
    return_1m REAL,
    return_3m REAL,
    return_6m REAL,
    max_drawdown REAL,
    volatility REAL,
    sharpe REAL,
    calmar REAL,
    drawdown_recovery_days INTEGER,
    risk_return_score REAL,
    holding_experience TEXT,
    source TEXT,
    source_mode TEXT NOT NULL DEFAULT 'SAMPLE',
    data_date TEXT NOT NULL,
    data_version TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(snapshot_date, symbol)
);
