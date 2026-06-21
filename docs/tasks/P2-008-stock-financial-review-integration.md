# P2-008: 股票财报事件与复盘闭链接入

- Status: TODO
- Priority: P2
- Owner: Codex
- Created At: 2026-06-21
- Completed At:

## Goal

让股票财报异常成为风险事件、重要事项、日报和 AI 解释输入。

## Scope

本任务只做财报事件识别与复盘闭链接入，不重做股票分析页。

## Concrete Changes

- 新增 `financial_event` 识别逻辑。
- 将重要财报异常写入 `risk_event`。
- 将重要财报异常生成 `review_task`。
- 将财报异常接入日报和 AI 解释。
- 按规则将财报异常影响建议等级。

## Acceptance

- 财报异常不会只停留在股票页面。
- 重要变化会进入复盘闭环。
- AI 只解释规则和数据依据，不自由生成建议。

## Verification

- 事件识别 smoke test。
- `risk_event` / `review_task` / 日报 / AI 链路验证。
- `rtk git diff --check`。

## Notes

- 不新增自动交易能力。
