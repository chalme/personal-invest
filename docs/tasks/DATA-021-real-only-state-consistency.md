# DATA-021: real-only 历史状态一致性修复

- Status: TODO
- Priority: P0
- Owner: Codex
- Created At: 2026-06-21

## Goal

修复页面仍大量出现 `sample` / `mixed` / `混合数据` 的历史残留状态。目标不是清空所有数据，而是选择性清理历史非真实污染、修正 manifest 与底层数据不一致、并把前端主视图从 sample/mixed 正常态收敛为真实数据、真实历史缓存、缺失和历史污染提示。

## Scope

- 扩展 `scripts/audit_real_only.py`。
- 扩展 `scripts/purge_non_real_data.py`。
- 检查并处理 `data/raw/market/*_manifest.json`、`data/raw/fund/*_manifest.json` 中的历史污染状态。
- 必要时调整 `backend/app/services/data_credibility_service.py` 的历史污染识别与降级口径。
- 必要时调整 `frontend/src/pages/Dashboard.tsx`、`frontend/src/pages/SettingsPage.tsx`、`frontend/src/components/ui.tsx` 的 sample/mixed 展示层级。

## Out of Scope

- 不清空 `storage/invest.db`。
- 不清空 `data/parquet/`。
- 不删除真实行情、真实基金净值、真实历史缓存、持仓、观察池、资产配置或人工录入数据。
- 不恢复 sample/mock/demo/estimated fallback。
- 不接入新真实数据源；真实行情多源容错由 `DATA-016` 到 `DATA-020` 覆盖。
- 不把历史污染简单隐藏；必须能在设置页或审计输出中定位。

## Current Findings

当前只读分析得到的残留点：

- `data/parquet/*` 当前没有非真实污染行。
- SQLite 仍有少量事件污染：
  - `financial_event`: `SAMPLE` 2 行，`ESTIMATED` 2 行。
  - `etf_deep_event`: `ESTIMATED` 3 行。
- 最新 raw manifest 仍可能包含历史污染状态：
  - `data/raw/market/2026-06-20_manifest.json`: `source_count.sample = 9`。
  - `data/raw/market/2026-06-21_manifest.json`: `source_mode = MIXED`，`source_count.sample = 8`。
- 前端仍有主视图展示 `样本`、`估算`、`混合数据` 的路径，导致页面观感上像是 sample 仍被正常使用。

## Concrete Changes

### 1. 补全 audit 覆盖范围

- `audit_real_only.py` 不应只维护固定表名单。
- 优先自动发现 SQLite 中所有包含 `source` 或 `source_mode` 字段的业务表。
- 至少必须覆盖：
  - `financial_event`
  - `etf_deep_event`
  - `fund_deep_event`
  - 现有财务、估值、质量、基金、ETF 快照表
- 识别以下非真实值：
  - `source_mode in ('SAMPLE', 'ESTIMATED')`
  - `source in ('sample', 'estimated', 'built_in_sample', 'deterministic_estimate', 'instrument_estimate', 'mock', 'demo')`
- 输出中区分：
  - SQLite 污染
  - Parquet 污染
  - manifest 污染

### 2. 补全 purge 覆盖范围

- `purge_non_real_data.py` 默认仍为 dry-run。
- 只有显式 `--apply` 才删除。
- SQLite 删除必须在事务中执行。
- 删除对象只限审计出的非真实行，不允许 truncate 整表。
- `--apply` 前必须创建备份或明确输出备份位置。
- 清理后重复执行应幂等。

### 3. 处理历史污染 manifest

- 审计脚本必须扫描 raw manifest：
  - `source_count.sample > 0`
  - `source_count.estimated > 0`
  - `source_mode in ('SAMPLE', 'ESTIMATED', 'MIXED')` 且 mixed 包含 sample/estimated
- purge 脚本可以选择：
  - 移动污染 manifest 到备份目录；或
  - 重写为历史污染标记并确保不再作为当前可信度来源。
- 处理策略必须保守：不能误删真实 raw 数据。

### 4. 收敛可信度 API 口径

- 可信度服务读取到历史污染 manifest 时：
  - `can_drive_advice = false`
  - 明确标记为历史污染或不可用于建议
  - 不把 sample/mixed 当作当前正常数据能力
- 如果底层 Parquet 已无 sample，但 manifest 仍旧，不能让 Dashboard 继续显示当前数据为 sample/mixed 正常态。

### 5. 收敛前端展示

- Dashboard 主视图不再大面积展示 `样本 x / 估算 x / 混合数据`。
- Dashboard 应优先展示：
  - 真实数据模块数
  - 真实历史缓存模块数
  - 缺失模块数
  - 不可驱动建议模块数
- 历史污染信息应下沉到 Settings 明细或治理提示。
- Settings 可以展示完整污染清单和建议操作。
- `DataModeBadge` 不应把 `MIXED` 展示成普通数据模式；如果 mixed 来自 sample/estimated，应展示为历史污染。

## Acceptance

- 不清空所有数据即可完成治理。
- `uv run python scripts/audit_real_only.py` 能扫描到所有 SQLite / Parquet / manifest 非真实污染。
- dry-run 能显示当前 `financial_event` 与 `etf_deep_event` 的污染行。
- `uv run python scripts/purge_non_real_data.py --apply` 清理后：
  - SQLite `SAMPLE` / `ESTIMATED` 污染行为 0。
  - Parquet `source=sample` / `source=estimated` 污染行为 0。
  - 最新有效 manifest 不再报告 `source_count.sample > 0` 作为当前正常状态。
- Dashboard 不再把 sample/mixed 作为主视图正常数据状态展示。
- Settings 能显示历史污染治理结果或明确无污染。
- 真实历史缓存 `akshare_cached` 仍保留并展示为真实历史缓存，但不能驱动高置信建议。

## Verification

- `git diff --check`
- `uv run python scripts/audit_real_only.py`
- `uv run python scripts/purge_non_real_data.py`
- `uv run python scripts/purge_non_real_data.py --apply`，仅在确认备份和 dry-run 输出后执行
- `uv run python scripts/audit_real_only.py` 再次确认污染为 0
- `uv run python -m compileall backend/app worker scripts`
- `pnpm -C frontend build`
- 手工或 smoke 验证 Dashboard / Settings 不再把 sample/mixed 当正常态展示

## Notes

本任务是历史状态一致性修复，不是数据源接入任务。核心边界是：只清非真实污染和过期污染状态，保留真实数据、真实历史缓存和人工数据。

