# P1-016: 低摩擦决策复盘闭环验收

- Status: DONE
- Priority: P1
- Owner: Codex
- Created At: 2026-06-21
- Completed At: 2026-06-21

## Goal

验证 P1-011 到 P1-015 的复盘闭环是否真的低打扰、可解释、可持续使用。

## Scope

本任务是验收 + 低风险修复。允许修复小型一致性、文案、状态流、空态和展示问题；不新增表、不新增大页面、不改核心模型。

## Concrete Changes

- 验证 `review_task` 去重、延后、解决、自动失效是否正确。
- 验证 `NO_MAJOR_RISK` 不会生成需要人工处理的重要事项。
- 验证 `SNOOZED` 到期后能重新进入关注范围。
- 验证 `decision_record` 表单足够轻量，并允许不关联 `review_task` 独立存在。
- 验证 `decision_outcome` 文案只表达后续表现和复盘参考，不写成决策正确或错误。
- 验证 Dashboard 只展示摘要，ReviewPage 承担完整复盘流程，Portfolio 只保留自然入口。

## Acceptance

- 同一重要事项不会重复刷屏。
- `OPEN`、`ACKNOWLEDGED`、`SNOOZED`、`RESOLVED`、`AUTO_EXPIRED` 状态展示和过滤正确。
- 用户可以记录系统内外触发的真实决策。
- outcome 只作为复盘参考，不被解释为业绩裁判。
- 没有重要事项时，页面明确显示暂无需要立即处理事项。
- 验收发现的小型体验或一致性问题可以在本任务内修复。

## Verification

- 后端 review API smoke test。
- ReviewService overview / tasks / decisions / outcomes 返回结构检查。
- 前端 Dashboard、ReviewPage、Portfolio 有数据、无数据、延后、解决和异常状态检查。
- `rtk ./scripts/check.sh`。

## Notes

- 本任务优先于股票财报和基金深度实现。
- 不把系统做成每日待办或打卡工具。
## Completion

- 验证迁移无待执行，重要事项生成器重复执行不会重复插入。
- 验证 `NO_MAJOR_RISK` 不会进入重要事项池或持久化事项。
- 验证 `decision_record` 可独立创建，不强制绑定 `review_task`。
- 修复复盘页只允许从重要事项记录决策的问题，新增“记录独立决策”入口。
- 验证 `decision_outcome` 文案保持为后续表现和复盘参考，不表达决策正确或错误。

## Changed Files

- `frontend/src/pages/ReviewPage.tsx`
- `docs/task-board.md`
- `docs/tasks/P1-016-review-loop-acceptance.md`

## Verification Result

- `uv run python scripts/migrate_db.py`
- `uv run python -m worker.review.task_generator`
- `uv run python -m worker.review.outcome_tracker`
- `PYTHONPATH=backend uv run python` smoke test for ReviewService overview and independent decision creation
- `cd frontend && pnpm build`
- `./scripts/check.sh`

