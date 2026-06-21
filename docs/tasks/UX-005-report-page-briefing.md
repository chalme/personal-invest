# UX-005: 日报投资简报化

- Status: TODO
- Priority: P2
- Owner: Codex
- Created At: 2026-06-21
- Completed At:

## Goal

将日报从 Markdown 阅读器升级为投资简报入口，首屏回答：今天最重要的变化是什么、有没有需要复核的风险、明天最应该关注什么。

## Scope

- 增加今日结论区。
- 展示重要事项、市场行业、资产分区和明日观察清单。
- 股票、ETF、FUND 分开解释。
- 保留 Markdown 原文归档。
- 展示整体 source mode 和低可信模块提示。

## Out of Scope

- 不重写报告生成体系。
- 不接新闻宏观源。
- 不做外部 LLM 长文生成。
- 不做复杂月报系统。

## Concrete Changes

- 报告页先展示简报摘要，再进入 Markdown 原文。
- 市场数据为 `SAMPLE` 时，顶部提示演示数据。
- 模块为 `MISSING` 时，该模块只显示缺失，不生成判断。
- 整体为 `MIXED` 时，提示哪些模块低可信。

## Acceptance

- 用户能在 30 秒内看到今天最重要变化和明日关注点。
- 日报不把低可信数据包装成确定性结论。
- 原 Markdown 报告仍可查看。

## Verification

- `pnpm -C frontend build`
- 检查有日报、无日报、MIXED 数据、MISSING 模块四类状态。
- `git diff --check`

## Notes

日报是聚合层，应在股票页、持仓页和观察池的信息结构稳定后执行。
