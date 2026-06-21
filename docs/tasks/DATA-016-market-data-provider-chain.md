# DATA-016: 真实行情多源 Provider 抽象

- Status: DONE
- Priority: P0
- Owner: Codex
- Created At: 2026-06-21

## Goal

把行情日线采集从单一 AKShare 接口调用升级为真实数据 provider chain。东方财富行情源不可用时，自动切换到腾讯等真实备用源；所有真实源失败时只能进入真实历史缓存或 `MISSING`，不能恢复 sample/mock/demo/estimated。

## Scope

- 主要修改 `worker/ingest/market_data.py`。
- 可按需要新增 `worker/ingest/market_providers.py`，但第一版应控制复杂度。
- 覆盖资产类型：A股、指数、ETF。
- 保留基金净值现有真实源链路，不在本任务重写基金净值。
- 保留 real-only 约束：任何失败路径都不能生成 sample。

## Out of Scope

- 不接入付费数据源。
- 不处理股票财务、基金画像、ETF 深度因子。
- 不做前端页面展示增强。
- 不做代理、出口 IP、服务器网络配置。
- 不清理历史数据污染。

## Concrete Changes

- 设计统一入口：`fetch_daily_bar(symbol, asset_type, start_date, end_date)`。
- 将现有 `_fetch_with_akshare()` 拆为资产类型路由和 provider chain。
- A股链路：
  - `stock_zh_a_hist`，东方财富。
  - `stock_zh_a_hist_tx`，腾讯备用。
  - 真实历史缓存。
  - `MISSING`。
- 指数链路：
  - `stock_zh_index_daily_tx`，腾讯优先或备用。
  - `stock_zh_index_daily`，新浪备用。
  - 真实历史缓存。
  - `MISSING`。
- ETF 链路：
  - `fund_etf_hist_em`，东方财富。
  - `stock_zh_a_hist_tx` 或 `stock_zh_index_daily_tx`，腾讯通用行情备用。
  - 真实历史缓存。
  - `MISSING`。
- 增加 symbol 转换：
  - `600519.SH` -> `sh600519`
  - `000001.SZ` -> `sz000001`
  - `000001.SH` -> `sh000001`
  - `399001.SZ` -> `sz399001`
  - `510300.SH` -> `sh510300`
- provider 成功必须返回 provider 元信息，供后续 manifest 和页面展示使用。

## Acceptance

- 东方财富股票接口失败时，`600519.SH` 可以通过腾讯真实源返回日线。
- 东方财富股票接口失败时，`000001.SZ` 可以通过腾讯真实源返回日线。
- `000001.SH` 和 `399001.SZ` 可以通过腾讯指数接口返回日线。
- 东方财富 ETF 接口失败时，`510300.SH` 可以通过腾讯真实源返回日线。
- 所有 provider 失败且无真实历史时，资产进入 `MISSING`，不生成 sample。
- 新同步结果不出现 `source=sample`、`source_mode=SAMPLE`、`deterministic_estimate`。
- 失败 provider 的错误类别和 fallback provider 被记录到 manifest 或日志中。

## Verification

- `uv run python -m compileall backend/app worker scripts`
- monkeypatch 东方财富失败、腾讯成功，验证 A股、指数、ETF 均写入真实数据。
- monkeypatch 所有 provider 失败且无历史，验证写入 `MISSING`，不写 sample parquet。
- 使用当前环境做只读探针，确认腾讯接口可返回真实历史行情。
- `git diff --check`

## Notes

本任务解决的是“真实数据源单点失败”问题，不降低 real-only 约束。数据源可以 fallback，数据真实性不能 fallback。


## Completion

- Completed At: 2026-06-21
- Implemented provider chain for real daily bars, provider metadata, missing field tracking, timeout/retry/circuit breaker, read-only probe script, and Dashboard/Settings provider credibility display.
- Real-only invariant preserved: all live providers failed -> real historical cache or MISSING, never sample/mock/demo/estimated.
