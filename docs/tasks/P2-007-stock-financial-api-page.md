# P2-007: 股票财报 API 与页面接入

- Status: DONE
- Priority: P2
- Owner: Codex
- Created At: 2026-06-21
- Completed At: 2026-06-21

## Goal

将股票财报、估值和公司质量快照接入后端 API 与股票分析页。

## Scope

本任务只做 API、service 和股票分析页展示，不负责财报事件入复盘闭环。

## Concrete Changes

- 增加股票财报摘要接口。
- 增加财务指标趋势接口。
- 增加估值分位接口。
- 增加公司质量摘要接口。
- 在股票分析页展示公司质量、估值位置、核心指标趋势、数据日期和来源。

## Acceptance

- 用户能在股票分析页看到财报和估值层信息。
- 接口结构稳定，可供 AI 和后续复盘复用。
- 页面明确展示数据来源和数据日期。

## Verification

- API smoke test。
- 股票分析页构建通过。
- `PYTHONPATH=backend uv run python` smoke tested `StockFinancialService`.
- `cd frontend && pnpm build`.
- `./scripts/check.sh`.

## Notes

- 不在本任务内新增复杂财报终端。
