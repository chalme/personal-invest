# 存储设计

## SQLite：业务状态库

SQLite 只保存小而重要、需要事务一致性的业务状态。

```text
schema_migration        数据库迁移记录
instrument              资产主数据
watchlist               观察池
portfolio_position      个人持仓
portfolio_snapshot      组合历史快照
trade_record            交易记录
strategy_config         策略配置
strategy_signal         策略信号
investment_advice       分级建议快照
risk_event              风险事件
market_trend_snapshot   市场趋势快照
sector_trend_snapshot   行业趋势快照
instrument_sector_map   资产行业/主题/指数/地区/风格映射
stock_analysis_snapshot 个股分析快照
fund_analysis_snapshot  基金分析快照
report_index            报告索引
job_execution           任务执行记录
ai_analysis             AI 分析记录
user_setting            用户配置
```

重要事项池 / review 当前是只读聚合能力，数据来自 `risk_event`、`investment_advice`、`portfolio_snapshot`、`job_execution` 和 `market_trend_snapshot`；第一版不新增 `review_task` 表。

## Parquet：分析明细库

```text
daily_bar               日线行情
fund_nav                基金净值
factor_value            因子数据
financial_indicator     财务指标
valuation_snapshot      估值快照
market_breadth          市场宽度
sector_factor           行业因子
stock_factor            个股因子
strategy_result         策略结果
backtest_trade          回测交易
backtest_position       回测持仓
```

## DuckDB：分析查询引擎

DuckDB 不做业务主库，只负责读取 Parquet 并做聚合分析。

用途：

- 全市场扫描
- 因子排序
- 行业强弱计算
- 回测统计
- 收益曲线
- 组合归因

## SQLite 配置

```sql
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA busy_timeout = 5000;
PRAGMA foreign_keys = ON;
```
