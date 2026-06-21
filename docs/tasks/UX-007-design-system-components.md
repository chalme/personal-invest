# UX-007: 设计系统与组件语言收敛

## Status

- Status: `DONE`
- Priority: `P1`
- Owner: `Codex`

## Goal

统一桌面端金融工作台的组件语言，让卡片、表格、Badge、按钮、空态、错误态、加载态和数据可信度标签在关键页面保持一致。

视觉优先级固定为：

```text
结论 > 风险 > 动作 > 证据 > 明细
```

## Scope

- 统一卡片层级、边框、间距和标题样式。
- 统一表格密度、排序、空态和低可信数据展示。
- 统一 Badge 和状态标签，尤其是数据可信度。
- 统一按钮层级：主动作、次动作、危险动作、仅查看动作。
- 统一加载、空状态、错误、任务失败和数据缺失文案。
- 保留现有 React / Vite / ECharts / lucide 技术栈。

## Data Credibility Labels

必须统一显示：

- `REAL`：真实数据，可以支撑高置信结论。
- `ESTIMATED`：估算数据，只能低置信解释。
- `SAMPLE`：样本数据，只能演示。
- `MISSING`：缺失数据，不生成确定性判断。
- `MIXED`：混合数据，必须说明哪些模块低可信。

## Out of Scope

- 不引入新前端框架。
- 不切换现有图标库。
- 不做品牌营销视觉。
- 不重写所有页面业务逻辑。
- 不做移动端专项。

## Acceptance Criteria

- Dashboard、股票页、持仓页、观察池、复盘页、日报和设置页的组件表达一致。
- 低可信数据不会被包装成高置信结论。
- 卡片和表格不再各自一套视觉语言。
- 空态、错误态、加载态和任务失败状态完整。
- 桌面端保持专业密度，而不是变成松散卡片墙。

## Completed At

- 2026-06-21

## Changed Files

- `frontend/src/components/ui.tsx`, `frontend/src/styles/global.css`, `frontend/src/pages/StocksPage.tsx`, `frontend/src/pages/PortfolioPage.tsx`, `frontend/src/pages/WatchlistPage.tsx`, `frontend/src/pages/ReportsPage.tsx`, `frontend/src/pages/SettingsPage.tsx`, `docs/task-board.md`, `docs/tasks/UX-007-design-system-components.md`

## Verification

- `pnpm -C frontend build`; `git diff --check`.

## Notes

- 新增统一 `Tone`、`DataModeBadge`、`FreshnessBadge`，补齐设计 token、结论卡、按钮、告警、设置表单和表格 hover 语言；不引入新前端框架。
- 本任务应在 `UX-006` 前后配合执行，避免导航和组件样式互相返工。
- 本项目不是 landing page，组件应服务长期使用和快速扫描。
