ALTER TABLE fund_analysis_snapshot ADD COLUMN analysis_type TEXT NOT NULL DEFAULT 'FUND_NAV';

UPDATE fund_analysis_snapshot
SET analysis_type = 'FUND_NAV'
WHERE analysis_type IS NULL OR analysis_type = '';
