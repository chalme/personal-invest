CREATE TABLE IF NOT EXISTS decision_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_date TEXT NOT NULL,
    symbol TEXT NOT NULL,
    name TEXT,
    asset_type TEXT NOT NULL,
    decision_type TEXT NOT NULL,
    decision_reason TEXT,
    expected_outcome TEXT,
    review_task_id INTEGER,
    advice_id INTEGER,
    advice_level TEXT,
    confidence REAL,
    conviction TEXT,
    data_date TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_decision_record_date ON decision_record(decision_date DESC);
CREATE INDEX IF NOT EXISTS idx_decision_record_symbol ON decision_record(symbol);
CREATE INDEX IF NOT EXISTS idx_decision_record_review_task ON decision_record(review_task_id);
