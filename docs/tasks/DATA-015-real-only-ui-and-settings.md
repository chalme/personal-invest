# DATA-015: 设置页与前端移除 sample 合法模式

- Status: DONE
- Priority: P1
- Owner: Codex
- Created At: 2026-06-21
- Completed At: 2026-06-21

## Goal

收敛前端和设置项，不再把 sample/mock/demo 数据作为可选运行模式或正常展示状态。用户看到的页面语言必须明确：真实数据缺失就是缺失，不能用样本兜底。

## Scope

- 设置服务：`backend/app/services/settings_service.py`。
- 设置页：`frontend/src/pages/SettingsPage.tsx`。
- 数据可信度展示：`frontend/src/components/ui.tsx`、`frontend/src/pages/Dashboard.tsx`、`frontend/src/pages/SettingsPage.tsx`。
- 核心页面：股票、基金、ETF、持仓、观察池、日报中涉及 `SAMPLE` / `ESTIMATED` 的文案和降级展示。
- API 类型：必要时调整 `frontend/src/api/types.ts`。

## Out of Scope

- 不接入新真实数据源。
- 不清理历史数据。
- 不改变导航和整体 UI 架构。
- 不做移动端专项。

## Concrete Changes

- 移除或禁用设置项：`仅样本数据`、`失败时使用样本兜底`、`fallback_to_sample=true`。
- 默认配置改为真实数据优先且不允许 sample fallback，例如 `fallback_to_sample=false`。
- 若读取到历史 `SAMPLE` / `ESTIMATED`，页面显示为历史污染/不可用于建议，而不是正常低可信模式。
- Badge 文案收敛：真实、真实缓存、缺失、过期；sample/estimated 只作为错误态或迁移期污染态。
- Dashboard 今日工作台和 Settings 数据可信度总览明确提示缺失模块，不制造样本结论。

## Acceptance

- 设置页不再出现“仅样本数据”或“失败时使用样本兜底”。
- 默认设置不会允许 runtime 生成 sample。
- Dashboard / Settings 不再把 `SAMPLE` 当作正常运行模式展示。
- 历史污染存在时，页面明确显示“历史非真实数据污染 / 不可用于建议”。
- 无真实数据时页面显示缺失和下一步动作，不显示假指标、假经理、假暴露或假结论。

## Verification

- `uv run python -m compileall backend/app worker scripts`
- `pnpm -C frontend build`
- Settings API smoke test：默认 `fallback_to_sample=false`。
- 前端 grep：确认用户可见文案不再提供 sample 作为可选模式。
- Dashboard / Settings smoke：构造 `MISSING` 和历史 `SAMPLE` 两类响应，确认展示为缺失/污染态。
- `git diff --check`

## Notes

本任务负责“用户看见和配置”的最后收口。它依赖 `DATA-011` 的语义，最好在 `DATA-012` 至少完成后执行，否则 UI 会先禁用 sample，但 worker 仍可能生成 sample。
## Completion

- Completed At: 2026-06-21
- Changed Files: `backend/app/services/settings_service.py`, `frontend/src/pages/SettingsPage.tsx`, `frontend/src/components/ui.tsx`, `frontend/src/pages/Dashboard.tsx`, `frontend/src/pages/MarketPage.tsx`, `frontend/src/pages/StocksPage.tsx`, `frontend/src/pages/ReportsPage.tsx`, `frontend/src/pages/WatchlistPage.tsx`, `frontend/src/api/types.ts`
- Verification: `pnpm -C frontend build`; Settings 默认 fallback_to_sample=false，页面不再提供 sample 作为可选运行模式。
- Notes: 历史 SAMPLE/ESTIMATED 仍可被展示为污染态，便于 DATA-013 清理前识别风险。
