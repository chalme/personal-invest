CREATE TABLE IF NOT EXISTS etf_profile (
    symbol TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    etf_type TEXT,
    tracking_index TEXT,
    theme TEXT,
    fund_company TEXT,
    listing_exchange TEXT,
    source TEXT,
    source_mode TEXT NOT NULL DEFAULT 'ESTIMATED',
    data_date TEXT NOT NULL,
    data_version TEXT,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS etf_exposure_snapshot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_date TEXT NOT NULL,
    symbol TEXT NOT NULL,
    name TEXT NOT NULL,
    exposure_type TEXT NOT NULL,
    exposure_name TEXT NOT NULL,
    weight REAL,
    exposure_note TEXT,
    source TEXT,
    source_mode TEXT NOT NULL DEFAULT 'ESTIMATED',
    data_date TEXT NOT NULL,
    data_version TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(snapshot_date, symbol, exposure_type, exposure_name)
);
