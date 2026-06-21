# DATA-007: 基金净值真实源稳定化

- Status: DONE
- Priority: P1
- Owner: Codex
- Created At: 2026-06-21
- Completed At: 2026-06-21

## Goal

提升场外基金净值同步稳定性，确保基金收益、回撤、持仓估值和复盘 outcome 不被样本净值误导。

## Scope

- 继续基于当前 AKShare / 本地 fallback 体系增强。
- AKShare 成功时记录 `REAL`。
- AKShare 失败但已有历史真实净值时，保留最近成功净值并输出 warning。
- 只有完全无历史净值时才使用样本兜底。
- fund manifest 必须包含最新净值日期、覆盖基金数、source mode、source count 和 warning。

## Out of Scope

- 不接付费基金源。
- 不抓基金公告。
- 不做基金画像真实源。
- 不改变基金深度分析模型。

## Concrete Changes

- 调整 `sync_fund_data()` 的失败处理和 fallback 边界。
- 数据可信度总览读取 fund manifest，稳定输出 `REAL` / `MIXED` / `SAMPLE` / `MISSING`。
- 基金页展示净值日期和 source mode。
- `SAMPLE` 基金净值只能用于演示，不能驱动高置信基金建议。

## Acceptance

- AKShare 失败时不会用样本覆盖已有真实净值。
- 无 active FUND 时安全显示缺失或无覆盖，不报错。
- 基金页和 Settings 能看到净值来源、日期和可信度。
- 基金净值数据过期或样本时，建议和日报明确降级。

## Verification

- `uv run python -m compileall backend/app worker scripts`
- smoke test `sync_fund_data()` manifest 输出。
- 构造 AKShare 不可用、有历史净值、无历史净值、无 FUND 四类场景。
- 检查 `/api/data/credibility` 中 `fund_nav` 可信度。

## Completed Changes

- `sync_fund_data()` 在 AKShare 基金净值同步失败时，先读取现有 `fund_nav` parquet 中的非 sample 历史净值。
- 有历史真实净值时写入 `akshare_cached`，保留最近成功净值，不再用 sample 静默覆盖。
- 无历史真实净值时才生成 sample。
- 无 active FUND 时继续安全写入 `MISSING` manifest，不报错。
- fund manifest 新增 `asset_source_status`，可追踪每只基金来自 `akshare`、`akshare_cached` 还是 `sample`。
- 出现 `akshare_cached` 时 `can_drive_advice=false`，并输出基金净值 fallback warning。

## Verification Result

- Passed: `uv run python -m compileall backend/app worker scripts`
- Passed: helper smoke test，确认 sample 净值历史不会被当作真实历史复用。
- Passed: monkeypatch `sync_fund_data()` smoke test，覆盖 AKShare 成功、复用历史、sample 兜底，manifest 输出 `MIXED`、`asset_source_status` 和 warning。
- Passed: `git diff --check`

## Notes

本任务复用 `DATA-003` 收敛的 manifest 和 fallback 口径。`akshare_cached` 表示真实历史保留，不等于当日新鲜真实净值；只要出现 cached fallback，就不能驱动高置信当日基金建议。
