# DATA-022: 接入 BaoStock 作为 A股真实历史行情补充源

- Status: TODO
- Priority: P1
- Owner: Codex
- Created At: 2026-06-21

## Goal

在 real-only 数据合约下，把 BaoStock 接入 A股日线 provider chain，作为 AKShare 东方财富/腾讯接口之外的免费真实历史行情补充源。目标是提升 A股日线可用性和字段完整度，但不替换 AKShare，不恢复 sample/mock/demo/estimated。

## Why

当前 AKShare 包本身可用，但不同底层公开源稳定性差异较大：东方财富行情源可能出现断连/超时，腾讯接口当前可用但字段较少。BaoStock 提供 A股历史 K 线和部分估值字段，适合补齐 A股日线真实数据链路。

核心矛盾：

- 真实行情需要更高可用性。
- 免费公开数据源天然不稳定。
- real-only 要求失败时只能进入真实备用源、真实历史缓存或 `MISSING`，不能回退 sample。

## Scope

- 在项目 data extra 中加入 BaoStock 依赖。
- 在行情 provider chain 中新增 BaoStock A股 provider。
- 支持 `600519.SH` / `000001.SZ` 等项目标准代码到 BaoStock 代码格式的转换。
- 标准化 BaoStock 返回字段到现有 daily bar schema。
- 写入 provider 元数据：`source_provider=baostock`、`source_interface=query_history_k_data_plus`、`missing_fields`、`fallback_reason`。
- 扩展只读健康探针，验证 BaoStock 是否可访问。
- 保持所有失败路径进入其他真实 provider、真实历史缓存或 `MISSING`。

## Out of Scope

- 不替换 AKShare。
- 不接入 Tushare Pro token 或付费数据源。
- 不接入 QUANTAXIS、QStock、Mootdx 作为本任务范围。
- 不实现实时行情。
- 不改基金净值、ETF 深度画像、财务因子主线。
- 不恢复 sample/mock/demo/estimated fallback。
- 不把 BaoStock 缺失字段估算成真实字段。

## Concrete Changes

### 1. Dependency

- 在 `pyproject.toml` 的 `data` extra 中加入 BaoStock。
- 更新 `uv.lock`。
- 保持基础运行不强制安装 data extra；只有数据同步和探针需要 `--extra data`。

### 2. Provider Chain

在 `worker/ingest/market_providers.py` 中新增 BaoStock A股 provider：

```text
A_STOCK:
  1. BaoStock query_history_k_data_plus
  2. AKShare Tencent stock_zh_a_hist_tx
  3. AKShare Eastmoney stock_zh_a_hist
  4. Local real cache
  5. MISSING
```

实际顺序可以按验证结果调整，但必须满足：所有 provider 都是真实源，不能恢复 sample fallback。

### 3. Symbol Mapping

支持项目内部代码：

```text
600519.SH -> sh.600519
000001.SZ -> sz.000001
```

非法或不支持代码必须明确返回 provider failure，不得静默生成数据。

### 4. Field Normalization

标准化 BaoStock 字段：

```text
date -> trade_date
open -> open
high -> high
low -> low
close -> close
volume -> volume
amount -> amount
turn -> turnover_rate
pctChg -> pct_chg
peTTM -> pe_ttm
pbMRQ -> pb_mrq
psTTM -> ps_ttm
pcfNcfTTM -> pcf_ncf_ttm
tradestatus -> trade_status
isST -> is_st
```

字段单位和缺失值必须记录清楚。真实源未返回或为空的字段写入 `missing_fields`，不能用估算值补齐。

### 5. Probe Script

扩展 `scripts/probe_market_sources.py`：

- 增加 BaoStock A股探针。
- 输出 provider、interface、symbol、status、rows、latest_date、error_class、elapsed_ms。
- 保持只读，不写 DB、Parquet 或 manifest。
- BaoStock 登录失败、查询失败、字段异常都要明确展示。

### 6. Manifest / Credibility

- manifest 的 `provider_count` 支持 `baostock`。
- 资产级状态能显示：

```text
REAL:baostock:query_history_k_data_plus
```

- 数据可信度 API 不应把 BaoStock 与 sample/estimated 混淆。

## Acceptance

- `600519.SH` 可通过 BaoStock 返回真实日线。
- `000001.SZ` 可通过 BaoStock 返回真实日线。
- BaoStock 成功时，daily bar 输出 `source_mode=REAL`、`source_provider=baostock`。
- manifest/provider metadata 能统计 `provider_count.baostock`。
- BaoStock 失败时继续尝试其他真实 provider；全部失败时只进入真实历史缓存或 `MISSING`。
- `source=sample`、`source_mode=SAMPLE`、`source_mode=ESTIMATED` 不会由本任务新增。
- `scripts/probe_market_sources.py` 能只读展示 BaoStock 可用性。
- Python 编译、ruff、相关 smoke 和前端构建通过。

## Verification

建议验证命令：

```bash
uv run python -m compileall backend/app worker scripts
uv run --extra dev ruff check worker/ingest/market_providers.py worker/ingest/market_data.py scripts/probe_market_sources.py
PYTHONDONTWRITEBYTECODE=1 uv run --extra data python scripts/probe_market_sources.py --timeout 12 --days 14
pnpm -C frontend build
git diff --check
```

建议 smoke：

- monkeypatch BaoStock 成功，确认 provider chain 返回 `REAL/baostock`。
- monkeypatch BaoStock 失败、腾讯成功，确认继续 fallback 到腾讯真实源。
- monkeypatch 全部真实 provider 失败，确认进入真实历史缓存或 `MISSING`。
- 检查 manifest 不包含 `sample` 或 `estimated` 正常运行状态。

## Notes

BaoStock 是 A股历史日线和估值字段补充源，不是 AKShare 的替代品。AKShare 继续保留广覆盖能力，BaoStock 只进入 provider chain 的真实源层。后续如需 Tushare Pro，应单独建任务并明确 token、授权、成本和合规边界。
