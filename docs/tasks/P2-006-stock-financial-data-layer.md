# P2-006: 股票财报数据层与快照

- Status: DONE
- Priority: P2
- Owner: Codex
- Created At: 2026-06-21
- Completed At: 2026-06-21

## Goal

落地股票财报、财务指标、估值和公司质量快照的数据层与 worker 计算链路。

## Scope

本任务只做数据库、worker 和基础 service 层，不接页面，不接复盘闭环展示。

## Concrete Changes

- 新增 `financial_statement_snapshot`。
- 新增 `financial_metric_snapshot`。
- 新增 `valuation_snapshot`。
- 新增 `stock_quality_snapshot`。
- 统一 `source`、`source_mode`、`data_date`、`data_version` 追溯字段。
- 在 daily job 中增加股票财报与估值快照计算步骤。

## Acceptance

- `STOCK` 资产能生成财报、指标、估值和质量快照。
- 缺失、样本、估算和真实数据能被区分。
- 后续 API 可直接读取这些快照。

## Verification

- `uv run python scripts/migrate_db.py` applied `011_stock_financial_snapshots`.
- `uv run python -m worker.factor.stock_financial` generated statement / metric / valuation / quality snapshots.
- Queried all four snapshot tables and confirmed rows exist.
- `uv run python -m compileall backend/app worker scripts`.
- `./scripts/check.sh`.

## Notes

- 不在本任务完成页面和复盘闭链接入。
