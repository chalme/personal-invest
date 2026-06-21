# UX-009: 核心页面逐页体验打磨

## Status

- Status: `DONE`
- Priority: `P2`
- Owner: `Codex`

## Goal

基于 UI 审计、导航重组和组件语言，对核心页面逐页打磨，让系统从“能用”提升到“长期使用舒服、清晰、可信”。

## Scope

- 股票页：研究结论优先，突出公司质量、趋势、估值、风险、建议和数据可信度。
- 持仓页：组合风险优先，突出暴露、集中度、盈亏、建议和复核入口。
- 观察池：研究状态优先，突出继续观察、降低关注、数据缺失和下一步观察。
- 复盘页：重要事项和决策记录优先，降低任务压力，强调后续表现只是复盘参考。
- 日报页：投资简报优先，先看结论和明日关注，再看 Markdown 原文。
- 设置页：数据源、任务、运行状态、主题和密度清晰分组。

## Out of Scope

- 不做全站重写。
- 不新增复杂业务能力。
- 不做移动端专项。
- 不把页面改成营销站。
- 不做华而不实的动画或装饰。

## Acceptance Criteria

- 每个核心页面都有清晰首屏问题和回答。
- 页面状态完整：有数据、无数据、数据异常、加载中、任务失败。
- 页面保留金融工作台信息密度，但不再散乱。
- 表格服务于明细，不压过结论、风险和动作。
- 低可信数据明确降级展示。

## Completed At

- 2026-06-21

## Changed Files

- `frontend/src/pages/StocksPage.tsx`, `frontend/src/pages/PortfolioPage.tsx`, `frontend/src/pages/WatchlistPage.tsx`, `frontend/src/pages/ReportsPage.tsx`, `frontend/src/pages/SettingsPage.tsx`, `frontend/src/styles/global.css`, `docs/task-board.md`, `docs/tasks/UX-009-core-page-polish.md`

## Verification

- `pnpm -C frontend build`; `git diff --check`.

## Notes

- 股票、持仓、观察池、日报、设置页的首屏结论/数据状态卡统一使用 `conclusion-card` 层级；本次为轻量逐页打磨，不做全站重写。
- 本任务应在 `UX-AUDIT-001`、`UX-006`、`UX-007` 和 `UX-008` 后执行。
- 如果范围过大，可以在执行时再拆成股票页、持仓页、观察池、复盘页、日报页和设置页子任务。
