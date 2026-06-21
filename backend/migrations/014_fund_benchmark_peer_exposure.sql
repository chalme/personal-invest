CREATE TABLE IF NOT EXISTS fund_benchmark_snapshot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_date TEXT NOT NULL,
    symbol TEXT NOT NULL,
    name TEXT NOT NULL,
    benchmark_name TEXT,
    fund_return_3m REAL,
    benchmark_return_3m REAL,
    excess_return_3m REAL,
    benchmark_score REAL,
    source TEXT,
    source_mode TEXT NOT NULL DEFAULT 'SAMPLE',
    data_date TEXT NOT NULL,
    data_version TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(snapshot_date, symbol)
);

CREATE TABLE IF NOT EXISTS fund_peer_rank_snapshot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_date TEXT NOT NULL,
    symbol TEXT NOT NULL,
    name TEXT NOT NULL,
    peer_group TEXT,
    percentile_3m REAL,
    percentile_6m REAL,
    peer_score REAL,
    peer_note TEXT,
    source TEXT,
    source_mode TEXT NOT NULL DEFAULT 'SAMPLE',
    data_date TEXT NOT NULL,
    data_version TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(snapshot_date, symbol)
);

CREATE TABLE IF NOT EXISTS fund_holding_exposure_snapshot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_date TEXT NOT NULL,
    symbol TEXT NOT NULL,
    name TEXT NOT NULL,
    exposure_type TEXT NOT NULL,
    exposure_name TEXT NOT NULL,
    weight REAL,
    overlap_note TEXT,
    source TEXT,
    source_mode TEXT NOT NULL DEFAULT 'SAMPLE',
    data_date TEXT NOT NULL,
    data_version TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(snapshot_date, symbol, exposure_type, exposure_name)
);
