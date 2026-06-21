# P2-011: 场外基金深度页与复盘闭链接入

- Status: TODO
- Priority: P2
- Owner: Codex
- Created At: 2026-06-21
- Completed At:

## Goal

将场外基金深度能力接入基金分析页、重要事项、日报和 AI 解释。

## Scope

本任务只针对 `FUND`，不推进 ETF 深度页面。

## Concrete Changes

- 在基金分析页增加基金画像、经理 / 公司、风险收益、基准 / 同类比较、风格暴露和持有体验模块。
- 将场外基金重要异常写入 `risk_event`。
- 将场外基金重要异常生成 `review_task`。
- 将场外基金深度结果接入日报和 AI 解释。

## Acceptance

- 用户能在基金分析页直接查看深度信息。
- 基金异常能进入复盘闭环。
- AI 只解释规则和数据依据。

## Verification

- 基金分析页构建通过。
- `risk_event` / `review_task` / 日报 / AI 链路验证。
- `rtk git diff --check`。

## Notes

- ETF 深度实现继续后置。
