# DATA-020: Dashboard / Settings 展示 provider 级可信度

- Status: DONE
- Priority: P2
- Owner: Codex
- Created At: 2026-06-21

## Goal

在 Dashboard 和设置页中展示真实行情来自哪个 provider、哪些资产使用真实历史缓存、哪些资产缺失，以及主要失败原因。页面不再只显示“真实/缺失”，还要解释真实源组成和 fallback 路径。

## Scope

- 修改 `frontend/src/pages/Dashboard.tsx`。
- 修改 `frontend/src/pages/SettingsPage.tsx`。
- 必要时修改 `frontend/src/components/ui.tsx`。
- 必要时修改 `frontend/src/api/types.ts`。
- 必要时读取后端已有数据可信度 API 中的新 manifest/provider 字段。

## Out of Scope

- 不改行情同步 provider chain。
- 不改 manifest 生成逻辑。
- 不新增图表库。
- 不恢复 sample / demo 展示模式。
- 不做移动端专项重构。

## Concrete Changes

- Dashboard 数据状态卡新增：
  - 真实源组成，例如 `腾讯 8 / 东方财富 0 / 真实缓存 1 / 缺失 0`。
  - 今日可用真实行情源。
  - 缓存资产数量。
  - 缺失资产数量。
- 设置页数据集明细新增：
  - `provider_count`
  - `interface_count`
  - 资产级 provider 状态。
  - 失败原因摘要。
- UI 语义收敛：
  - `真实源：腾讯`
  - `真实源：东方财富`
  - `真实历史缓存`
  - `缺失`
  - `接口失败`
  - `字段缺失`
- 页面遇到历史污染字段时继续显示为不可用于建议，不把 sample / estimated 作为合法模式。

## Acceptance

- Dashboard 能看到当前行情真实源组成。
- 设置页能看到 provider_count 和失败原因摘要。
- 缺失资产能被列出或汇总。
- `akshare_cached` / `REAL_CACHED` 明确展示为真实历史缓存，且不能驱动高置信建议。
- 页面不出现“仅样本数据”“失败时使用样本兜底”等合法化文案。
- 前端构建通过。

## Verification

- `pnpm -C frontend build`
- 使用 mock API 或现有开发数据验证 provider_count 展示。
- 验证缺失字段为空时页面不崩溃。
- 验证历史污染态仍显示为不可用于建议。
- `git diff --check`

## Notes

本任务是可观测性和用户理解增强。它不负责让数据源变可用，数据源容错由 `DATA-016` 到 `DATA-019` 负责。


## Completion

- Completed At: 2026-06-21
- Implemented provider chain for real daily bars, provider metadata, missing field tracking, timeout/retry/circuit breaker, read-only probe script, and Dashboard/Settings provider credibility display.
- Real-only invariant preserved: all live providers failed -> real historical cache or MISSING, never sample/mock/demo/estimated.
