# P2-002: 桌面端主题与密度系统

- Status: DONE
- Priority: P2
- Owner: Codex
- Created At: 2026-06-21
- Completed At: 2026-06-21

## Goal

建立桌面端主题、信息密度和视觉一致性基础，让投资工作台在桌面浏览时更清晰、更稳定、更适合长期使用。

## Scope

本任务只处理桌面端体验，不做移动端响应式适配。

包括：

- 亮 / 暗主题变量。
- 标准 / 紧凑信息密度。
- 卡片、表格、图表、状态徽标和页面间距统一。
- 设置页保存 UI 偏好。
- Dashboard、观察池、持仓、股票、基金、复盘等核心页面的桌面端视觉一致性。

不包括：

- 移动端导航。
- 底部 Tab。
- 抽屉侧边栏。
- 触摸交互优化。
- 小屏重排和断点系统。

移动端后续另拆 `P2-016`。

## Concrete Changes

- 扩展全局 CSS 变量，支持 light / dark theme。
- 增加 density token，统一 normal / compact 的间距和字体密度。
- 在 Settings 页面增加主题和密度设置入口。
- 确认设置能持久化到现有设置体系。
- 梳理核心页面卡片、表格和图表容器的桌面端展示。

## Acceptance

- 桌面端主题切换后页面可读性稳定。
- 标准 / 紧凑密度切换后表格和卡片间距明显变化。
- 核心页面视觉层级一致，不出现明显断裂的卡片、表格或图表间距。
- 设置刷新后仍保持用户选择。
- 不引入移动端响应式改动。
- `cd frontend && pnpm build` 通过。
- `./scripts/check.sh` 当前环境缺少 `node/pnpm`，未完成前端阶段。

## Changed Files

- `frontend/src/App.tsx`
- `frontend/src/pages/SettingsPage.tsx`
- `frontend/src/utils/uiPreferences.ts`
- `frontend/src/styles/global.css` 通过。

## Verification

- `cd frontend && pnpm build`
- `./scripts/check.sh` 当前环境缺少 `node/pnpm`，未完成前端阶段。

## Changed Files

- `frontend/src/App.tsx`
- `frontend/src/pages/SettingsPage.tsx`
- `frontend/src/utils/uiPreferences.ts`
- `frontend/src/styles/global.css`
- 手动检查 Dashboard、Watchlist、Portfolio、Stocks、Funds、Review、Settings 的桌面端展示。

## Notes

- 原 `P2-002` 只是保留编号，现在重定义为桌面端体验任务。
- 移动端适配暂不执行。
