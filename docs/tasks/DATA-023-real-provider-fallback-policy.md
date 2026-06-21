# DATA-023: 历史行情真实源 fallback 策略标准化

## Status

`TODO`

## Priority

`P1`

## Owner

`Codex`

## Goal

把历史行情同步的真实数据 provider chain 固化为明确策略：东方财富不可用时自动尝试腾讯、BaoStock、Sina 等真实备用源；所有真实源失败时只能使用本地真实历史缓存或进入 `MISSING`，禁止恢复 sample/mock/demo/estimated。

## Background

当前系统已经完成 real-only 第一阶段，也已经有多源行情 provider 抽象。但后续开发需要更明确的策略文档和实现边界，避免不同模块各自决定 fallback 顺序，造成：

- 东财断连后直接失败，而不是继续尝试真实备用源。
- 腾讯字段少时被错误补齐为真实字段。
- worker、probe、manifest、UI 对 provider 状态解释不一致。
- 未来任务误把 sample 或 estimated 当成兜底。

本任务聚焦 **历史日线 / 同步链路**，不处理用户点击持仓录入时的实时报价。

## Target Provider Chain

### A股日线

```text
BaoStock
  -> AKShare Eastmoney stock_zh_a_hist
  -> AKShare Tencent stock_zh_a_hist_tx
  -> REAL_CACHED
  -> MISSING
```

### 指数日线

```text
AKShare Tencent stock_zh_index_daily_tx
  -> AKShare Sina stock_zh_index_daily
  -> REAL_CACHED
  -> MISSING
```

### ETF / 场内基金日线

```text
AKShare Eastmoney fund_etf_hist_em
  -> AKShare Tencent compatible daily source
  -> REAL_CACHED
  -> MISSING
```

## Scope

- Review and standardize provider order in `worker/ingest/market_providers.py`.
- Ensure `worker/ingest/market_data.py` records provider attempts, fallback reason, missing fields and final source mode.
- Ensure `scripts/probe_market_sources.py` can show provider health in the same vocabulary used by ingestion.
- Ensure manifests expose enough information for data credibility pages and reports.
- Ensure fallback never fabricates missing fields.

## Out of Scope

- 不接付费数据源。
- 不新增自动交易能力。
- 不处理持仓录入实时报价；该部分由 `QUOTE-004` 覆盖。
- 不恢复 sample/mock/demo/estimated fallback。
- 不清空全库或通过删除数据掩盖旧污染。

## Data Contract

Provider result must include:

```text
provider
interface
source_mode
fallback_level
fallback_reason
missing_fields
error_category
elapsed_ms
```

允许的最终状态：

```text
REAL
REAL_CACHED
STALE
MISSING
```

禁止作为正常结果：

```text
SAMPLE
MOCK
DEMO
ESTIMATED
```

## Acceptance Criteria

- 东财 A股日线失败时，worker 继续尝试 BaoStock 或腾讯真实源。
- 指数同步优先使用腾讯真实接口，失败后再尝试 Sina，全部失败进入 `REAL_CACHED` 或 `MISSING`。
- ETF 日线同步优先走 ETF 专用真实源，失败后可尝试腾讯兼容源或本地真实缓存。
- 腾讯字段缺失时写入 `missing_fields`，不得伪造换手率、涨跌额、成交额等字段。
- manifest 记录 provider 尝试列表、最终 provider、fallback reason、missing fields。
- 数据可信度服务能区分 provider fallback 与 sample 污染。
- `scripts/probe_market_sources.py` 输出 provider 状态与 ingestion manifest 术语一致。

## Verification

```bash
git diff --check
uv run python -m compileall worker scripts backend/app
PYTHONPATH=backend:. uv run python scripts/probe_market_sources.py --timeout 8
```

可选 smoke：模拟 Eastmoney provider 失败，确认真实备用源继续执行，且最终结果不是 sample。

## Notes

- 本任务是历史行情 pipeline 标准化，不代表所有 provider 都必须同时可用。
- Fallback 的目标是提高真实数据可用性，不是降低真实性要求。

