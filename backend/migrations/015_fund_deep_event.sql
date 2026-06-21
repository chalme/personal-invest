CREATE TABLE IF NOT EXISTS fund_deep_event (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_date TEXT NOT NULL,
    symbol TEXT NOT NULL,
    name TEXT NOT NULL,
    event_type TEXT NOT NULL,
    severity INTEGER NOT NULL DEFAULT 2,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    source_mode TEXT NOT NULL,
    source_snapshot_date TEXT,
    data_version TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(event_date, symbol, event_type)
);
