# P2-013: ETF 流动性与风险收益快照

- Status: TODO
- Priority: P2
- Owner: Codex
- Created At: 2026-06-21
- Completed At:

## Goal

为 ETF / LOF 生成流动性、阶段收益、回撤、波动和交易风险快照。

## Scope

本任务只做数据模型、worker 和 service 读取，不接页面、AI、日报或复盘闭环。

第一版优先使用已有 `daily_bar` 和可得元数据，避免依赖实时盘口。

## Concrete Changes

- 新增 ETF 流动性快照表，如 `etf_liquidity_snapshot`。
- 新增 ETF 风险收益快照表，如 `etf_risk_return_snapshot`。
- 计算成交额、成交量、规模、阶段收益、最大回撤、波动和流动性风险等级。
- 输出 `source_mode`、`data_version`、`data_date`。
- daily job 接入 ETF 流动性和风险收益计算步骤。

## Acceptance

- ETF 能解释交易活跃度、阶段表现、回撤和波动。
- 缺失成交额、规模或价格序列时，不生成高置信度结论。
- 不影响 `FUND` 深度分析，也不回写股票财报相关表。
- 无 ETF / LOF 时 worker 安全跳过。

## Verification

- `uv run python scripts/migrate_db.py`
- `uv run python -m worker.etf.liquidity_risk_return`
- 查询 ETF 流动性和风险收益表。
- `uv run python -m compileall backend/app worker scripts`
- `./scripts/check.sh`

## Notes

- 实时买卖价差、盘口深度和申赎数据后置。
