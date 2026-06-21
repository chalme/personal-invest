# DATA-003: 行情日线稳定性增强

- Status: TODO
- Priority: P1
- Owner: Codex
- Created At: 2026-06-21
- Completed At:

## Goal

提升股票、ETF、指数日线同步稳定性，避免真实数据失败时被样本数据静默覆盖。

## Scope

- 继续基于当前 AKShare / 本地 fallback 体系增强。
- AKShare 成功时记录 `REAL`。
- AKShare 失败但已有历史真实数据时，保留最近成功数据并输出 warning。
- 只有完全无历史数据时才使用样本数据兜底。
- market manifest 必须表达 `REAL` / `MIXED` / `SAMPLE` / `MISSING`、覆盖资产数、最新数据日期和 warning。

## Out of Scope

- 不接新供应商。
- 不做实时行情或分钟线。
- 不改 Parquet 主存储方向。
- 不重写市场/行业分析模型。

## Concrete Changes

- 调整 `worker/ingest/market_data.py` 的失败处理和 fallback 边界。
- 保持 `daily_bar` 现有 Parquet 输出结构兼容。
- 数据可信度服务优先使用 manifest source mode，不再仅依赖文件存在判断。
- 页面继续展示来源和日期，避免样本行情被包装成真实行情。

## Acceptance

- AKShare 部分失败时，不覆盖已有真实历史。
- 全样本行情显示 `SAMPLE`。
- 真实和样本混合显示 `MIXED`。
- 无数据时显示 `MISSING`。
- 价格类高置信建议只基于可接受的新鲜真实数据。

## Verification

- `uv run python -m compileall backend/app worker scripts`
- smoke test `sync_market_data()` manifest 输出。
- 构造 AKShare 不可用、部分资产失败、无历史数据三类场景。
- 检查 `/api/data/credibility` 中 `daily_bar` 和 `market_data` 可信度。

## Notes

本任务依赖 `DATA-004` 的新鲜度口径。若先单独执行，也必须保留未来接入 freshness 的接口位置。
