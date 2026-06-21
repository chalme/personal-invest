# P1-011: Review Task 持久化

- Status: TODO
- Priority: P1
- Owner: Codex
- Created At: 2026-06-21
- Completed At:

## Goal

把当前只读的重要事项聚合沉淀为可追踪的 `review_task`，让系统能记住“当时提醒了什么、是否处理、是否已经失效”。

## Scope

第一版只做重要事项沉淀，不做完整任务管理系统。UI 文案继续使用“重要事项、复核、延后、已解决”，避免变成每日待办。

## Concrete Changes

- 新增 `review_task` 表，包含 `dedupe_key`、事项类型、优先级、状态、资产信息、来源信息、建议动作、创建/更新时间、确认/延后/解决/过期时间。
- 从现有 `ReviewService` 聚合结果生成持久化事项，并使用 `dedupe_key` 防止重复生成。
- 新增 worker 入口 `worker/review/task_generator.py`，daily job 在建议和风险生成后调用。
- API 支持读取事项列表和更新状态。
- `NO_MAJOR_RISK` 不生成 `review_task`。

## Acceptance

- 同一资产同一日期同类事项不会重复刷屏。
- 状态支持 `OPEN`、`ACKNOWLEDGED`、`SNOOZED`、`RESOLVED`、`AUTO_EXPIRED`。
- `SNOOZED` 有 `snoozed_until`，未到期默认不出现在 OPEN 列表。
- 事项有 `expires_at`，可自动进入 `AUTO_EXPIRED`。

## Verification

- 迁移重复执行幂等。
- 手动调用生成逻辑两次，不产生重复事项。
- 只有 `NO_MAJOR_RISK` 时不生成事项。
- Python 编译和前端构建通过。

## Notes

- `review_task` 是重要事项沉淀表，不是每日待办表。
