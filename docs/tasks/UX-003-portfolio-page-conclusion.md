# UX-003: 持仓页组合决策化

- Status: DONE
- Priority: P2
- Owner: Codex
- Created At: 2026-06-21
- Completed At: 2026-06-21

## Goal

将持仓页从持仓表升级为组合风险和复核入口，首屏回答：当前组合最大风险是什么、哪些持仓需要优先处理。

## Scope

- 增加组合风险结论。
- 突出优先复核资产。
- 展示资产类型暴露、行业/主题集中度和单一资产集中度。
- 展示盈亏贡献和风险对应关系。
- 保留持仓明细表作为下层内容。

## Out of Scope

- 不做复杂收益归因。
- 不做交易归因。
- 不做多账户。
- 不做交易导入。
- 不改持仓数据模型。

## Concrete Changes

- 首屏展示整体风险、最大单一风险、是否需要介入。
- 减仓关注、卖出关注、仓位过重、回撤扩大等资产进入优先复核区。
- 价格/净值不是 `REAL` 时，盈亏和仓位提示标记为低置信。
- ETF 暴露为 `ESTIMATED` 时，只提示主题暴露，不做精确集中度结论。

## Acceptance

- 用户能快速看到是否需要介入。
- 用户能看到哪些持仓优先复核。
- 页面不把低可信估值当成确定性盈亏结论。
- Portfolio 只做复盘入口，不变成第二个 ReviewPage。

## Verification

- `pnpm -C frontend build`
- 检查有持仓、无持仓、低可信价格/净值、存在高风险事项四类状态。
- `git diff --check`

## Completed Changes

- 持仓页首屏新增“组合决策结论”卡。
- 展示当前最大风险、优先复核持仓数、最大持仓、集中度状态。
- 将严重风险、减仓/卖出关注、仓位过重、大幅浮亏持仓归入优先复核资产。
- 增加资产类型暴露摘要，保留持仓明细表作为下层内容。
- 明确价格/净值低可信时只做估算展示，不包装成确定性盈亏结论。

## Verification Result

- Passed: `git diff --check`
- Passed: `uv run python -m compileall backend/app worker scripts`
- Not run: `pnpm -C frontend build`，当前执行环境缺少 `node` / `pnpm`。

## Notes

本任务复用股票页结论化的信息表达方式，只调整持仓页信息结构，不改变持仓数据模型，不替代 ReviewPage。
