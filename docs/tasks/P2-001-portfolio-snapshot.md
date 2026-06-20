# P2-001: 新增组合历史快照

- Status: DONE
- Priority: P2
- Owner: Codex
- Created At: 2026-06-21
- Completed At: 2026-06-21

## Goal

每日沉淀组合总览，支持组合曲线、风险变化、建议摘要和日报复盘。

## Scope

- 新增 `backend/migrations/007_portfolio_snapshot.sql`。
- 新增 `portfolio_snapshot` 表。
- 第一版只做日级总览。
- 快照包含 `snapshot_date`、`account_id`、`total_market_value`、`total_cost`、`total_pnl`、`total_pnl_ratio`、`stock_value`、`etf_value`、`fund_value`、`concentration_hhi`、`risk_count`、`advice_summary`、`created_at`。
- 每日任务生成组合快照。

## Out Of Scope

- 不做多账户。
- 不做现金管理。
- 不做行业归因、收益归因或交易归因。
- 不替代当前 `portfolio_position`。

## Acceptance

- 每日任务能生成当天组合快照。
- 快照能区分股票、ETF 和基金市值。
- 快照包含集中度、风险数和建议摘要。
- 报告和后续页面可以读取快照做历史复盘。

## Completion Markers

- Completed At: 2026-06-21
- Changed Files:
- Verification:
- Notes:

