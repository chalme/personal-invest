# 技术架构

## 最终技术栈

```text
FastAPI
+ React / Vite
+ shadcn 风格组件 / Tailwind CSS
+ ECharts
+ TanStack Table
+ SQLite
+ DuckDB
+ Parquet
+ APScheduler
+ Markdown / HTML Reports
+ AI Assistant
```

## 总体架构

```text
Browser
  │
  ▼
React / Vite / Tailwind / ECharts
  │
  ▼
FastAPI API Server
  │
  ├── Dashboard API
  ├── Market Trend API
  ├── Sector Trend API
  ├── Stock Analysis API
  ├── Fund Analysis API
  ├── Watchlist API
  ├── Portfolio API
  ├── Signal API
  ├── Backtest API
  ├── Report API
  └── AI Analysis API
  │
  ├── SQLite
  │   └── 业务状态 / 持仓 / 观察池 / 信号摘要 / 报告索引
  │
  ├── DuckDB
  │   └── 本地分析查询
  │
  ├── Parquet
  │   └── 行情 / 基金净值 / 因子 / 财务 / 回测明细
  │
  ├── Markdown / HTML
  │   └── 日报 / 周报 / 分析报告
  │
  └── APScheduler
      └── 每日收盘任务
```

## 模块边界

股票、ETF 和场外基金的业务定义以 `business-information-architecture.md` 为准；本文件只描述技术模块和数据流。

| 模块 | 职责 |
|---|---|
| Dashboard | 展示市场、持仓、信号、风险总览 |
| Market Trend | 判断大盘趋势、市场宽度、量能、情绪 |
| Sector Trend | 判断行业强弱、轮动、行业风险 |
| Stock Analysis | 分析个股趋势、基本面、估值、资金、风险 |
| Fund Analysis | 分析基金收益、回撤、波动、类型适配、风险 |
| Watchlist | 管理股票和基金观察池、分组、备注、优先级 |
| Portfolio | 管理持仓、成本、盈亏、仓位 |
| Signal | 管理策略信号、观察标记、风险提示 |
| Backtest | 验证策略历史表现 |
| Report | 生成日报、周报、HTML/Markdown 报告 |
| AI Assistant | 基于系统数据做解释，不做交易决策 |

## 每日任务流

```text
收盘后
  │
  ▼
同步行情 / 财务 / 行业 / 资金 / 公告
  │
  ▼
同步基金净值 / 基金元数据
  │
  ▼
保存 raw 原始数据
  │
  ▼
清洗写入 Parquet
  │
  ▼
计算市场趋势
  │
  ▼
计算行业强弱
  │
  ▼
计算个股分析
  │
  ▼
计算基金分析
  │
  ▼
生成策略信号
  │
  ▼
执行持仓风控
  │
  ▼
生成日报 / 周报
  │
  ▼
页面展示
```

## 一致性底线

1. raw 原始数据永远不覆盖。
2. Parquet 写入先写 tmp，再 rename。
3. 策略信号必须记录 data_version。
4. 报告必须记录 data_date、source、generated_at。
5. 回测禁止未来函数。
6. AI 只能解释数据，不能直接下单。
7. 页面必须显示当前数据日期和更新时间。
8. 股票和基金必须有明确 asset_type，基金分析不能套用股票基本面/估值口径。

## 任务文档分层

```text
docs/product-backlog.md     长期产品需求池
docs/operation-backlog.md   长期运维需求池
docs/task-board.md          当前执行看板
docs/tasks/*.md             复杂任务详情页
```
