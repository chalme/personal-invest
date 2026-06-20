CREATE TABLE IF NOT EXISTS schema_migration (
    version TEXT PRIMARY KEY,
    name TEXT,
    applied_at TEXT NOT NULL
);
