# UX-005: 日报投资简报化

- Status: DONE
- Priority: P2
- Owner: Codex
- Created At: 2026-06-21
- Completed At: 2026-06-21

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

## Completed Changes

- 报告页首屏新增“今日投资简报”卡。
- 简报卡展示最重要变化、是否需要复核、明日先看和数据边界。
- 从日报 Markdown 中提取市场、行业、股票、基金和 ETF 分区摘要，原 Markdown 归档继续保留。
- 报告页读取数据可信度总览，整体 `MIXED`、`SAMPLE`、`MISSING` 时在顶部提示数据边界。
- `report_builder` 在 Markdown 顶部新增“投资简报”段，报告内容可追溯，不依赖前端临时判断。

## Verification Result

- Passed: `git diff --check`
- Passed: `uv run python -m compileall backend/app worker scripts`
- Passed: `PYTHONPATH=backend uv run python` import smoke test for `build_daily_report`
- Not run: `pnpm -C frontend build`，当前执行环境缺少 `node` / `pnpm`。

## Notes

日报是聚合层，本任务只强化简报入口和 Markdown 归档关系，不接新闻宏观源、不引入外部 LLM 长文生成。
