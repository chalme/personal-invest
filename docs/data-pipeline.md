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
    "sample": 0
  },
  "source_mode": "REAL | SAMPLE | MIXED | MISSING",
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

`DataCredibilityService` 应优先读取 manifest 中的 `source_mode`；缺失时再根据 `source_count` 推导。这样 market、fund 和后续真实数据源可以复用同一套可信度判断逻辑。
