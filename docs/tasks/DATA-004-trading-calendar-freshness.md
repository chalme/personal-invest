# DATA-004: 交易日历与数据新鲜度 V1

- Status: TODO
- Priority: P1
- Owner: Codex
- Created At: 2026-06-21
- Completed At:

## Goal

建立统一交易日历和数据新鲜度判断，让系统能解释当前行情、净值和分析快照是否落在最近有效交易日。

## Scope

- 增加最近有效交易日判断。
- 无真实交易日历时按工作日估算，并标记为 `ESTIMATED`。
- 为数据可信度结果补充 `expected_latest_trade_date`、`freshness_status`、`stale_days`、`can_drive_advice` 和 `warning`。
- Dashboard 和 Settings 展示数据是否新鲜、是否能驱动高置信建议。

## Out of Scope

- 不接付费交易日历。
- 不做节假日维护 UI。
- 不接宏观日历或公告日历。
- 不重写所有建议规则。

## Concrete Changes

- 后端增加统一 freshness 计算逻辑，优先服务 `daily_bar`、`market_data`、`fund_nav` 和数据可信度总览。
- 数据过期时，数据可信度模块应显示低可信提示。
- 建议和重要事项可读取 `can_drive_advice`，但第一版不要求重写所有策略分支。

## Acceptance

- 系统能回答“最新数据日期”和“预期最近交易日”。
- 数据落后时显示 `STALE` 或等价状态。
- 非交易日不应误判为数据过期。
- 无真实交易日历时明确展示估算口径。

## Verification

- `uv run python -m compileall backend/app worker scripts`
- `PYTHONPATH=backend uv run python` smoke test freshness 计算。
- 构造工作日、周末、缺失数据、旧数据日期场景。
- 如前端可用，执行 `pnpm -C frontend build`。

## Notes

这是后续行情稳定、基金净值稳定和页面结论化的基础任务。
