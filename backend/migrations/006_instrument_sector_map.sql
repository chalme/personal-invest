CREATE TABLE IF NOT EXISTS instrument_sector_map (
    symbol TEXT NOT NULL,
    map_type TEXT NOT NULL DEFAULT 'SECTOR',
    sector_code TEXT NOT NULL,
    sector_name TEXT NOT NULL,
    weight REAL,
    source TEXT,
    updated_at TEXT NOT NULL,
    PRIMARY KEY(symbol, map_type, sector_code)
);

INSERT OR IGNORE INTO instrument_sector_map(symbol, map_type, sector_code, sector_name, weight, source, updated_at)
SELECT
    symbol,
    'SECTOR',
    UPPER(REPLACE(COALESCE(NULLIF(sector_code, ''), NULLIF(sector_name, ''), 'UNMAPPED'), ' ', '_')),
    COALESCE(NULLIF(sector_name, ''), NULLIF(sector_code, ''), '未分组'),
    1.0,
    COALESCE(source, 'INSTRUMENT'),
    COALESCE(updated_at, datetime('now'))
FROM instrument
WHERE symbol IS NOT NULL AND symbol != ''
  AND (sector_code IS NOT NULL OR sector_name IS NOT NULL);

INSERT OR IGNORE INTO instrument_sector_map(symbol, map_type, sector_code, sector_name, weight, source, updated_at)
SELECT
    symbol,
    'SECTOR',
    UPPER(REPLACE(COALESCE(NULLIF(group_name, ''), 'UNMAPPED'), ' ', '_')),
    COALESCE(NULLIF(group_name, ''), '未分组'),
    1.0,
    'WATCHLIST_GROUP',
    COALESCE(updated_at, datetime('now'))
FROM watchlist
WHERE status = 'ACTIVE' AND symbol IS NOT NULL AND symbol != '';
