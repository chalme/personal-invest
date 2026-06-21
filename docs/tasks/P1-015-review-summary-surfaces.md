# P1-015: 复盘摘要接入 Dashboard / Portfolio

- Status: TODO
- Priority: P1
- Owner: Codex
- Created At: 2026-06-21
- Completed At:

## Goal

把持久化重要事项、最近决策和 outcome 摘要接入 Dashboard 与 Portfolio，但让 ReviewPage 继续作为完整复盘主入口。

## Scope

Dashboard 只展示摘要，不做完整处理流程。Portfolio 只提供按资产记录决策和查看相关事项的入口，不塞满复盘交互。

## Concrete Changes

- Dashboard 展示 OPEN 重要事项数量、高优先级摘要、最近决策和数据异常状态。
- Portfolio 页在持仓资产上显示相关重要事项和“记录决策”入口。
- ReviewPage 展示完整事项列表、决策历史和 outcome 摘要。
- 周/月复盘摘要优先使用 `review_task`、`decision_record` 和 `decision_outcome`。

## Acceptance

- 用户 30 秒内能知道是否需要介入。
- Dashboard 不变成任务处理页。
- 持仓页可以自然进入记录决策流程。
- ReviewPage 是复盘闭环的主入口。

## Verification

- 前端构建通过。
- Dashboard 有事项、无事项、任务失败、数据异常状态展示正确。
- Portfolio 中持仓资产能进入记录决策。

## Notes

- 本任务是低摩擦决策复盘闭环 V1 的收口任务。
