# UX-004: 观察池研究状态化

- Status: DONE
- Priority: P2
- Owner: Codex
- Created At: 2026-06-21
- Completed At: 2026-06-21

## Goal

将观察池从资产列表升级为研究状态视图，首屏回答：正在研究什么、哪些值得继续观察、哪些关注已经失效。

## Scope

- 增加观察池摘要。
- 展示高优先级、风险升高、数据缺失、长期未更新资产。
- 资产列表展示关注理由、建议等级、最新变化和下一步观察。
- 支持按股票、ETF、FUND 筛选。
- 增加数据待补齐分组。

## Out of Scope

- 不做复杂标签系统。
- 不做批量导入。
- 不做自动清理。
- 不改观察池数据库结构。

## Concrete Changes

- 样本数据资产不进入高优先级机会排序。
- 数据缺失资产进入“数据待补齐”分组。
- 估算暴露只作为辅助标签。
- 降低优先级、暂停关注、移除等清理动作只按现有能力表达，不新增复杂工作流。

## Acceptance

- 用户能一眼看出观察池研究状态。
- 用户能区分值得继续观察、风险升高、数据缺失和关注失效资产。
- 页面不制造每日待办压力。

## Verification

- `pnpm -C frontend build`
- 检查空观察池、有 STOCK/ETF/FUND、低可信数据、风险升高四类状态。
- `git diff --check`

## Completed Changes

- 观察池首屏新增“观察池研究状态”卡。
- 按优先级、状态、关注理由和分组字段将资产分为重点研究、数据待补齐、低优先级和关注失效。
- 展示资产类型分布、值得继续观察资产、待补齐 / 待清理资产和下一步观察。
- 资产列表增加研究状态和下一步观察列。
- 不新增标签系统、不改数据库结构、不做自动清理。

## Verification Result

- Passed: `git diff --check`
- Passed: `uv run python -m compileall backend/app worker scripts`
- Not run: `pnpm -C frontend build`，当前执行环境缺少 `node` / `pnpm`。

## Notes

本任务复用股票页和持仓页的结论化表达，只做前端研究状态分层，不制造每日待办压力。
