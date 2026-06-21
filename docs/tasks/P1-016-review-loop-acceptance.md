# P1-016: 低摩擦决策复盘闭环验收

- Status: TODO
- Priority: P1
- Owner: Codex
- Created At: 2026-06-21
- Completed At:

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
