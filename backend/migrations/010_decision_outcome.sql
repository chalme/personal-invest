CREATE TABLE IF NOT EXISTS decision_outcome (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_id INTEGER NOT NULL,
    horizon TEXT NOT NULL,
    measured_at TEXT NOT NULL,
    price_at_decision REAL,
    price_at_measure REAL,
    return_ratio REAL,
    advice_level_at_decision TEXT,
    advice_level_at_measure TEXT,
    risk_count_at_decision INTEGER,
    risk_count_at_measure INTEGER,
    summary TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(decision_id, horizon)
);

CREATE INDEX IF NOT EXISTS idx_decision_outcome_decision ON decision_outcome(decision_id);
CREATE INDEX IF NOT EXISTS idx_decision_outcome_measured ON decision_outcome(measured_at DESC);
