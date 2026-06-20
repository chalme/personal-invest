CREATE TABLE IF NOT EXISTS instrument (
    symbol TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    asset_type TEXT NOT NULL DEFAULT 'STOCK',
    market TEXT,
    exchange TEXT,
    sector_code TEXT,
    sector_name TEXT,
    fund_type TEXT,
    risk_level TEXT,
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    source TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

INSERT OR IGNORE INTO instrument(symbol, name, asset_type, market, sector_name, status, source, created_at, updated_at)
SELECT
    symbol,
    COALESCE(NULLIF(name, ''), symbol),
    COALESCE(NULLIF(asset_type, ''), 'STOCK'),
    market,
    group_name,
    'ACTIVE',
    'WATCHLIST',
    COALESCE(created_at, datetime('now')),
    COALESCE(updated_at, datetime('now'))
FROM watchlist
WHERE symbol IS NOT NULL AND symbol != '';

INSERT OR IGNORE INTO instrument(symbol, name, asset_type, status, source, created_at, updated_at)
SELECT
    symbol,
    COALESCE(NULLIF(name, ''), symbol),
    COALESCE(NULLIF(asset_type, ''), 'STOCK'),
    'ACTIVE',
    'PORTFOLIO',
    COALESCE(updated_at, datetime('now')),
    COALESCE(updated_at, datetime('now'))
FROM portfolio_position
WHERE symbol IS NOT NULL AND symbol != '';

INSERT OR IGNORE INTO instrument(symbol, name, asset_type, risk_level, status, source, created_at, updated_at)
SELECT
    symbol,
    COALESCE(NULLIF(name, ''), symbol),
    COALESCE(NULLIF(asset_type, ''), 'STOCK'),
    risk_level,
    'ACTIVE',
    'SIGNAL',
    COALESCE(created_at, datetime('now')),
    COALESCE(created_at, datetime('now'))
FROM strategy_signal
WHERE symbol IS NOT NULL AND symbol != '';

INSERT OR IGNORE INTO instrument(symbol, name, asset_type, status, source, created_at, updated_at)
SELECT
    symbol,
    COALESCE(NULLIF(name, ''), symbol),
    COALESCE(NULLIF(asset_type, ''), 'STOCK'),
    'ACTIVE',
    'ADVICE',
    COALESCE(created_at, datetime('now')),
    COALESCE(created_at, datetime('now'))
FROM investment_advice
WHERE symbol IS NOT NULL AND symbol != '';
