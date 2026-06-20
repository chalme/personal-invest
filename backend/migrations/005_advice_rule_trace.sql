ALTER TABLE investment_advice ADD COLUMN rule_code TEXT NOT NULL DEFAULT 'personal_advice_v1';
ALTER TABLE investment_advice ADD COLUMN rule_version TEXT NOT NULL DEFAULT '1.0.0';
ALTER TABLE investment_advice ADD COLUMN strategy_code TEXT NOT NULL DEFAULT 'personal_watch_v1';
ALTER TABLE investment_advice ADD COLUMN source_snapshot_type TEXT;
ALTER TABLE investment_advice ADD COLUMN source_snapshot_date TEXT;
ALTER TABLE investment_advice ADD COLUMN previous_advice_level TEXT;
ALTER TABLE investment_advice ADD COLUMN change_reason TEXT;
ALTER TABLE investment_advice ADD COLUMN rule_result TEXT;
