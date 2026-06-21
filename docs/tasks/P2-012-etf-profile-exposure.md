# P2-012: ETF 画像与暴露数据层

- Status: TODO
- Priority: P2
- Owner: Codex
- Created At: 2026-06-21
- Completed At:

## Goal

为 ETF / LOF 建立独立画像与暴露数据层，补齐跟踪指数、主题、行业、地区、风格和资产类别暴露。

## Scope

本任务只做数据模型、回填和 worker 快照，不接页面、AI、日报或复盘闭环。

ETF 已有 `ETF_PRICE` 基础分析；本任务进一步补充 ETF 专项主数据和暴露结构。

## Concrete Changes

- 新增 ETF 画像表，如 `etf_profile`。
- 新增 ETF 暴露快照表，如 `etf_exposure_snapshot`。
- 从 `instrument`、观察池和已有 ETF 数据回填 ETF / LOF。
- 记录跟踪指数、主题、行业、地区、风格和资产类别暴露。
- 每条快照包含 `source_mode`、`data_version`、`data_date`。
- daily job 接入 ETF 画像和暴露生成步骤。

## Acceptance

- ETF 不进入股票财报模型。
- ETF 不进入场外基金经理模型。
- ETF 能解释跟踪指数、主题和主要暴露。
- 没有真实暴露数据时明确标记 `ESTIMATED` 或 `MISSING`，不伪装成真实数据。
- 无 ETF / LOF 时 worker 安全跳过。

## Verification

- `uv run python scripts/migrate_db.py`
- `uv run python -m worker.etf.profile_exposure`
- 查询 ETF 画像和暴露表。
- `uv run python -m compileall backend/app worker scripts`
- `./scripts/check.sh`

## Notes

- 这是 ETF 深度分析 V1 的数据底座。
- 复杂指数成分和精确持仓穿透可后续增强。
