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

默认优先尝试 AKShare。环境未安装 AKShare、网络失败或接口异常时，系统自动降级为本地样本行情，确保开发和页面演示不中断。

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
    "akshare_cached": 0,
    "sample": 0
  },
  "source_mode": "REAL | SAMPLE | MIXED | MISSING",
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

- 只有非 `sample` 来源：`REAL`
- 同时存在真实来源和 `sample`：`MIXED`
- 只有 `sample`：`SAMPLE`
- 没有数据或没有来源：`MISSING`

`akshare_cached` 表示本次真实源同步失败，但保留了最近一次成功写入的真实历史数据。它仍属于非样本真实来源，因此不把 `source_mode` 降为 `SAMPLE`；但只要出现 `akshare_cached`，`can_drive_advice` 必须降为 false，并在 `warning` 中提示相关资产不能驱动高置信当日价格建议。

`DataCredibilityService` 应优先读取 manifest 中的 `source_mode`；缺失时再根据 `source_count` 推导。这样 market、fund 和后续真实数据源可以复用同一套可信度判断逻辑。

## 交易日历与新鲜度口径

第一版不接付费交易日历，`expected_latest_trade_date` 按工作日估算：如果今天是周末，则回退到最近一个工作日；如果今天是工作日，则使用今天。因此 `trade_calendar_source_mode` 固定为 `ESTIMATED`，页面必须提示未纳入法定节假日或临时休市。

日频数据模块使用统一状态：

- `FRESH`：`latest_data_date >= expected_latest_trade_date`。
- `STALE`：`latest_data_date < expected_latest_trade_date`，`stale_days` 按工作日差计算。
- `MISSING`：缺少数据或缺少可判断日期。
- `NOT_APPLICABLE`：非日频数据，不参与交易日新鲜度判断。

`can_drive_advice` 只有在 `source_mode=REAL` 且 `freshness_status=FRESH` 时才能为 true。`SAMPLE`、`MIXED`、`MISSING` 或 `STALE` 数据只能用于展示、低置信解释或缺失提示，不能驱动高置信建议。

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
