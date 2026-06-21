# P1-013: Decision Record

- Status: TODO
- Priority: P1
- Owner: Codex
- Created At: 2026-06-21
- Completed At:

## Goal

记录用户真实投资决策及原因，让系统能在周/月复盘中回答“当时为什么这么做”。

## Scope

第一版只做轻量决策记录，不做交易执行、不做多账户、不替代完整交易流水。

## Concrete Changes

- 新增 `decision_record` 表。
- 支持决策类型：`BUY`、`HOLD`、`REDUCE`、`SELL`、`NO_ACTION`。
- 决策可选关联 `review_task` 和 `investment_advice`，也允许独立存在。
- 记录资产、决策原因、预期结果、信心、当时建议等级和数据日期。
- `ReviewPage` 增加记录决策入口，`PortfolioPage` 可提供按资产记录决策入口。

## Acceptance

- 用户可以记录系统提醒触发的决策，也可以记录系统外触发的决策。
- 决策记录能关联当时的重要事项、建议和资产。
- 前端表单保持轻量，只要求动作、原因和信心，其余字段尽量自动带入。

## Verification

- 迁移重复执行幂等。
- API 能创建和读取决策记录。
- 前端构建通过。
- 买入、持有、减仓、卖出、暂不处理五种动作都能保存。

## Notes

- 数据库存英文枚举，前端展示中文。
