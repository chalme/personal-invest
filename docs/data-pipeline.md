# 数据流水线

当前每日任务已经形成可运行闭环：

```text
sync_market_data
  -> data/raw/market/*_manifest.json
  -> data/parquet/daily_bar/
  -> calculate_market_trend
  -> calculate_sector_trend
  -> calculate_stock_analysis
  -> generate_signals
  -> run_risk_check
  -> reports/daily/YYYY-MM-DD.md
```

## 数据源策略

系统执行 real-only 策略：开发和线上都只使用真实数据、真实历史缓存或缺失态。真实源失败时可以切换其他真实 provider；全部真实源失败且没有真实历史缓存时，必须标记 `MISSING`，不能生成 sample、mock、demo 或 estimated 数据。

安装真实数据源能力：

```bash
uv sync --extra data
```

## 存储边界

- `raw`：采集清单和原始元数据，不覆盖。
- `Parquet`：行情、市场宽度、行业因子、个股因子。
- `SQLite`：市场趋势快照、行业快照、个股分析快照、信号、风险、报告索引。

## 风控边界

所有信号只代表观察，不代表自动交易。AI 只能解释已有数据，不能绕过风控。

## Manifest 可信度口径

所有 raw manifest 后续应尽量保持统一最小结构：

```json
{
  "dataset": "daily_bar | fund_nav | ...",
  "generated_at": "ISO timestamp",
  "latest_data_date": "YYYY-MM-DD",
  "rows": 0,
  "asset_count": 0,
  "source_count": {
    "akshare": 0,
    "baostock": 0,
    "tencent": 0,
    "sina": 0,
    "akshare_cached": 0,
    "missing": 0
  },
  "provider_count": {
    "baostock": 0,
    "eastmoney": 0,
    "tencent": 0,
    "sina": 0,
    "ttfund": 0,
    "akshare_cached": 0,
    "missing": 0
  },
  "source_mode": "REAL | REAL_CACHED | MISSING",
  "expected_latest_trade_date": "YYYY-MM-DD",
  "trade_calendar_source_mode": "REAL | ESTIMATED",
  "freshness_status": "FRESH | STALE | MISSING | NOT_APPLICABLE",
  "stale_days": 0,
  "can_drive_advice": true,
  "warning": "可选中文说明"
}
```

兼容字段可以继续保留，例如：

- `latest_trade_date`
- `latest_nav_date`
- `symbols`
- `funds`

`source_mode` 推导规则：

- 当前真实 provider 同步成功：`REAL`。
- 本次真实源失败但存在真实历史缓存：`REAL_CACHED`。
- 没有可用真实数据：`MISSING`。
- 历史 `SAMPLE` / `ESTIMATED` / sample-mixed manifest 只能作为污染态进入审计和清理流程，不能作为正常运行时状态。

`akshare_cached` 表示本次真实源同步失败，但保留了最近一次成功写入的真实历史数据。它可以展示为真实历史缓存，但 `can_drive_advice` 必须降为 false，并在 `warning` 中提示相关资产不能驱动高置信当日价格建议。

`DataCredibilityService` 应优先读取 manifest 中的 `source_mode`；缺失时再根据 `source_count` 推导。这样 market、fund 和后续真实数据源可以复用同一套可信度判断逻辑。

## 交易日历与新鲜度口径

第一版不接付费交易日历，`expected_latest_trade_date` 按工作日估算：如果今天是周末，则回退到最近一个工作日；如果今天是工作日，则使用今天。因此 `trade_calendar_source_mode` 固定为 `ESTIMATED`，页面必须提示未纳入法定节假日或临时休市。

日频数据模块使用统一状态：

- `FRESH`：`latest_data_date >= expected_latest_trade_date`。
- `STALE`：`latest_data_date < expected_latest_trade_date`，`stale_days` 按工作日差计算。
- `MISSING`：缺少数据或缺少可判断日期。
- `NOT_APPLICABLE`：非日频数据，不参与交易日新鲜度判断。

`can_drive_advice` 只有在 `source_mode=REAL` 且 `freshness_status=FRESH` 时才能为 true。`REAL_CACHED`、`MISSING` 或 `STALE` 数据只能用于展示、低置信解释或缺失提示，不能驱动高置信建议。

## 真实数据源增强拆解

真实数据源增强不应一次性做成大任务。后续按 `DATA-003` 到 `DATA-010` 分批推进：

| 任务 | 主题 | 第一输出 |
|---|---|---|
| `DATA-003` | 行情日线稳定性增强 | `daily_bar` + market manifest |
| `DATA-004` | 交易日历与数据新鲜度 | 交易日历 / freshness 判断 |
| `DATA-005` | 股票真实财报源 | 财报与财务指标快照 |
| `DATA-006` | 股票估值真实数据 | 估值快照与历史分位 |
| `DATA-007` | 基金净值真实源稳定化 | `fund_nav` + fund manifest |
| `DATA-008` | 基金画像真实数据源 | 基金画像、经理、公司 |
| `DATA-009` | ETF 跟踪指数与指数行情 | ETF 跟踪质量 |
| `DATA-010` | ETF 折溢价与规模 | ETF 折溢价、规模、流动性 |

每个任务都必须明确：输入、输出、`source_mode`、fallback、页面影响和建议规则影响。


## Real-only Runtime Policy

投资系统的运行时数据策略是：线上和开发环境只使用真实数据或真实历史缓存。缺少真实数据时必须显示 `MISSING` / 不可用，不能为了页面完整性自动生成 sample、mock、demo 或 deterministic estimate 数据。

### Allowed Runtime States

| State | Meaning | Display | Can Drive High-confidence Advice |
|---|---|---|---|
| `REAL` / `akshare` | 当前同步成功的真实源数据 | 正常展示 | 取决于新鲜度 |
| `REAL_CACHED` / `akshare_cached` | 真实历史缓存，通常来自上次成功同步 | 展示为真实历史缓存 | 否 |
| `STALE` | 有真实数据但晚于预期最近交易日 | 展示为过期 | 否 |
| `MISSING` | 没有可用真实数据 | 展示缺失和下一步动作 | 否 |

### Forbidden Runtime States

以下状态不能由 worker、API、页面或开发环境 runtime 正常产生或依赖：

- `SAMPLE`
- `ESTIMATED`
- `MIXED` 中包含 sample / estimated 的正常态
- `built_in_sample`
- `deterministic_estimate`
- mock/demo 数据进入 `data/`、`storage/`、报告、建议或前端页面

测试可以使用 fixture，但必须隔离在测试目录或显式测试上下文，不能写入本地开发数据目录或生产数据目录。

### Fallback Decision Table

| Situation | Correct Behavior | Forbidden Behavior |
|---|---|---|
| 真实源成功 | 写入真实数据和 manifest | 同时混入 sample |
| 真实源失败，有真实历史 | 复用真实历史缓存，标记 cached/stale，关闭高置信建议 | 把历史 sample 当缓存 |
| 真实源失败，无真实历史 | 标记 `MISSING`，页面显示缺失 | 生成 sample/mock/demo |
| 财报/基金画像/ETF 深度数据未接入真实源 | 不写假快照，API 返回缺失态 | 写 `SAMPLE` / `ESTIMATED` 分数或画像 |
| 页面读取到历史 sample/estimated | 显示历史污染/不可用于建议 | 当作低可信但正常的数据模式 |

### Execution Tasks

Real-only 治理按以下任务推进：

1. `DATA-011`：真实数据 only 策略与 source mode 合约。
2. `DATA-012`：禁止行情与基金净值新增 sample 生成。
3. `DATA-013`：历史 sample / estimated 数据审计与清理脚本。
4. `DATA-014`：股票 / 基金 / ETF 非真实因子改为 `MISSING`。
5. `DATA-015`：设置页与前端移除 sample 合法模式。

## 真实行情多源容错阶段

Real-only 治理完成后，下一阶段重点从“禁止造样本”升级为“真实行情多源容错”。数据源可以 fallback，但数据真实性不能 fallback。

### Provider Chain Principle

行情同步必须遵守：

```text
真实主源 -> 真实备用源 -> 真实历史缓存 -> MISSING
```

禁止：

```text
真实源失败 -> sample/mock/demo/estimated
```

第一版推荐链路：

| Asset Type | Primary Provider | Real Fallback | Final Fallback |
|---|---|---|---|
| A股 | 东方财富 `stock_zh_a_hist` | 腾讯 `stock_zh_a_hist_tx` | 真实历史缓存 / `MISSING` |
| 指数 | 腾讯 `stock_zh_index_daily_tx` | 新浪 `stock_zh_index_daily` | 真实历史缓存 / `MISSING` |
| ETF | 东方财富 `fund_etf_hist_em` | 腾讯通用行情接口 | 真实历史缓存 / `MISSING` |
| 基金净值 | 天天基金 / 东方财富 `fund_open_fund_info_em` | 真实历史缓存 | `MISSING` |

### Provider Metadata

日线和 manifest 应逐步补充 provider 级元数据：

```json
{
  "source_mode": "REAL | REAL_CACHED | MISSING",
  "source_provider": "eastmoney | tencent | sina | ttfund | akshare_cached | missing",
  "source_interface": "stock_zh_a_hist_tx",
  "missing_fields": [],
  "derived_fields": [],
  "fallback_reason": "eastmoney_remote_disconnected",
  "provider_count": {
    "eastmoney": 0,
    "tencent": 0,
    "sina": 0,
    "akshare_cached": 0,
    "missing": 0
  }
}
```

`source_mode=REAL` 只表示数据来自真实外部源，不表示每个字段都完整。真实源未提供的字段必须进入 `missing_fields`，不能用估算值伪造。

### Execution Tasks

真实行情多源容错按以下任务推进：

1. `DATA-016`：真实行情多源 Provider 抽象。
2. `DATA-017`：行情字段标准化与 provider 元数据。
3. `DATA-018`：行情源健康检查脚本。
4. `DATA-019`：行情同步 timeout / retry / 熔断。
5. `DATA-020`：Dashboard / Settings 展示 provider 级可信度。

## Real-only 历史状态一致性修复

真实数据 only 和真实行情多源容错完成后，仍可能出现历史状态不一致：底层 Parquet 已无 sample，但旧 manifest、事件表或前端主视图仍显示 `sample` / `mixed` / `混合数据`。这类问题不能通过清空所有数据解决，必须选择性清理历史污染并保留真实数据与人工数据。

### Cleanup Principle

允许清理：

- `source_mode=SAMPLE` / `source_mode=ESTIMATED` 的历史运行时记录。
- `source=sample` / `source=estimated` / `source=built_in_sample` / `source=deterministic_estimate` 的历史运行时记录。
- 明确包含 `source_count.sample > 0` 或 sample/estimated `MIXED` 的过期 manifest。

禁止清理：

- 真实行情、真实基金净值、真实历史缓存。
- 持仓、观察池、资产配置、设置、人工录入资产。
- 整个 SQLite、整个 Parquet 目录或整个 raw 目录。

### Execution Task

1. `DATA-021`：real-only 历史状态一致性修复。

验收口径：审计脚本覆盖 SQLite / Parquet / manifest；清理脚本默认 dry-run，`--apply` 才执行；清理后污染为 0；Dashboard 不再把 sample/mixed 作为正常主视图状态，Settings 保留治理明细。

## BaoStock A股真实源补强

AKShare 继续作为广覆盖公开数据入口，但不能把任何单一底层公开源当作稳定唯一来源。东方财富行情接口不可用或字段异常时，系统应优先切换其他真实源，而不是退回 sample。BaoStock 可作为 A股历史日线和部分估值字段的免费真实补充源。

### Target Positioning

BaoStock 定位为：

- A股历史日线真实 provider。
- A股估值字段补充 provider。
- AKShare 东方财富 / 腾讯接口之外的 provider chain 成员。

BaoStock 不定位为：

- AKShare 替代品。
- 基金净值、ETF 深度画像或实时行情主源。
- sample/mock/demo/estimated fallback。

### Provider Order

A股日线建议链路：

```text
BaoStock query_history_k_data_plus
  -> AKShare Tencent stock_zh_a_hist_tx
  -> AKShare Eastmoney stock_zh_a_hist
  -> local real cache
  -> MISSING
```

真实源顺序可以按实测稳定性调整，但所有节点都必须是真实公开源或真实历史缓存。

### Field Boundary

BaoStock 返回字段可以补强：

- OHLCV / amount。
- `turn` / `pctChg`。
- `peTTM` / `pbMRQ` / `psTTM` / `pcfNcfTTM`。
- `tradestatus` / `isST`。

真实源未提供或为空的字段必须进入 `missing_fields`，不能通过估算伪造成真实字段。

### Execution Task

1. `DATA-022`：接入 BaoStock 作为 A股真实历史行情补充源。

验收口径：`600519.SH`、`000001.SZ` 可通过 BaoStock 返回真实日线；manifest 能显示 `provider_count.baostock`；BaoStock 失败时继续走其他真实 provider、真实历史缓存或 `MISSING`；全链路不产生 sample/mock/demo/estimated。
