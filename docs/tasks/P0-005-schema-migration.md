# P0-005: 建立轻量迁移体系

- Status: DONE
- Priority: P0
- Owner: Codex
- Created At: 2026-06-21
- Completed At: 2026-06-21

## Goal

建立可重复执行的数据库迁移机制，让后续新增表和字段不再混入 `001_init.sql` 或临时补列逻辑。

## Scope

- 新增 `backend/migrations/002_schema_migration.sql`。
- 新增 `schema_migration(version, name, applied_at)`。
- 新增 `scripts/migrate_db.py` 作为轻量迁移 runner。
- `scripts/init_db.py` 在基础初始化后调用迁移。
- 后续迁移文件使用稳定命名，例如 `003_instrument.sql`、`004_fund_analysis_type.sql`。

## Out Of Scope

- 不新增业务字段。
- 不创建 `instrument`、`investment_advice` 追溯字段或其他业务表。
- 不删除旧初始化逻辑。

## Acceptance

- 重复执行 `scripts/migrate_db.py` 不报错。
- 已执行迁移会记录到 `schema_migration`。
- 已执行迁移不会重复应用。
- P0-005 的提交只包含迁移基础设施，不混入业务模型改造。

## Completion Markers

- Completed At: 2026-06-21
- Changed Files:
- Verification:
- Notes:

