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
