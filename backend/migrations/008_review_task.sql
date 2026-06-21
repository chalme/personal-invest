CREATE TABLE IF NOT EXISTS review_task (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dedupe_key TEXT NOT NULL UNIQUE,
    task_type TEXT NOT NULL,
    priority TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'OPEN',
    symbol TEXT,
    name TEXT,
    asset_type TEXT,
    title TEXT NOT NULL,
    summary TEXT,
    source_type TEXT NOT NULL,
    source_id TEXT,
    source_date TEXT,
    data_version TEXT,
    review_reason TEXT,
    suggested_action TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    acknowledged_at TEXT,
    snoozed_until TEXT,
    resolved_at TEXT,
    expires_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_review_task_status_priority ON review_task(status, priority, source_date);
CREATE INDEX IF NOT EXISTS idx_review_task_symbol ON review_task(symbol);
CREATE INDEX IF NOT EXISTS idx_review_task_source ON review_task(source_type, source_id);
