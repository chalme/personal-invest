# 文档索引

本文是 `docs/` 目录入口。主 README 负责快速介绍和启动，本索引负责把文档按使用场景分组。

## 先读什么

| 场景 | 推荐文档 |
|---|---|
| 第一次使用系统 | [`user-guide.md`](user-guide.md) |
| 想看当前交易账本实现规格 | [`specs/trading-ledger-mvp-v1.6.md`](specs/trading-ledger-mvp-v1.6.md) |
| 想理解长期北极星 | [`strategy/investment-behavior-operating-system.md`](strategy/investment-behavior-operating-system.md) |
| 想理解关键架构取舍 | [`decisions/`](decisions/) |
| 想知道系统支持哪些功能 | [`feature-matrix.md`](feature-matrix.md) |
| 想理解数据源和 real-only 策略 | [`data-sources.md`](data-sources.md) / [`data-pipeline.md`](data-pipeline.md) |
| 想理解系统限制 | [`limitations.md`](limitations.md) |
| 想评估成本和风险 | [`cost-and-risk.md`](cost-and-risk.md) |
| 想查看 API 能力 | [`api.md`](api.md) |
| 想开发或部署 | [`development.md`](development.md) |
| 想做生产排障 | [`operations-runbook.md`](operations-runbook.md) |
| 想提交或发布 | [`release-checklist.md`](release-checklist.md) |
| 想看当前任务 | [`task-board.md`](task-board.md) |

## 用户与产品文档

| 文档 | 说明 |
|---|---|
| [`purpose.md`](purpose.md) | 项目目的、目标用户、非目标 |
| [`user-guide.md`](user-guide.md) | 页面使用手册和每日操作流程 |
| [`feature-matrix.md`](feature-matrix.md) | 功能矩阵、状态、数据依赖和限制 |
| [`limitations.md`](limitations.md) | 投资、数据、架构、安全和运维限制 |
| [`cost-and-risk.md`](cost-and-risk.md) | 成本结构、免费源风险和商业取舍 |
| [`business-information-architecture.md`](business-information-architecture.md) | 股票、ETF、场外基金的信息架构和业务边界 |
| [`business-roadmap.md`](business-roadmap.md) | 观察资产、持仓、组合复盘和分级建议规划 |

## 技术与数据文档

| 文档 | 说明 |
|---|---|
| [`architecture.md`](architecture.md) | 技术架构、模块边界、数据流 |
| [`specs/trading-ledger-mvp-v1.6.md`](specs/trading-ledger-mvp-v1.6.md) | 当前冻结版轻量交易账本实现规格 |
| [`decisions/`](decisions/) | 已接受的关键架构判断和取舍 |
| [`data-sources.md`](data-sources.md) | AKShare / BaoStock / 腾讯 / 新浪等真实数据源说明 |
| [`data-pipeline.md`](data-pipeline.md) | 每日流水线、manifest、real-only、provider chain |
| [`storage.md`](storage.md) | SQLite / DuckDB / Parquet 存储边界 |
| [`api.md`](api.md) | API 分组、路由、读写边界和使用示例 |
| [`development.md`](development.md) | 本地开发、服务器启动、生产部署 |
| [`operations-runbook.md`](operations-runbook.md) | 生产运维、健康检查、备份恢复、故障排查 |
| [`release-checklist.md`](release-checklist.md) | 提交、验证、发布、回滚检查清单 |

## 分析模型设计

| 文档 | 说明 |
|---|---|
| [`stock-financial-analysis-design.md`](stock-financial-analysis-design.md) | 股票财报、估值、质量和财报事件设计 |
| [`fund-deep-analysis-design.md`](fund-deep-analysis-design.md) | 场外基金画像、经理/公司、风险收益和同类比较设计 |
| [`etf-deep-analysis-design.md`](etf-deep-analysis-design.md) | ETF / LOF 指数、主题、流动性、跟踪质量和交易风险设计 |

## 策略与历史治理

| 文档 | 说明 |
|---|---|
| [`strategy/investment-behavior-operating-system.md`](strategy/investment-behavior-operating-system.md) | 投资行为操作系统 10 层长期北极星 |
| [`specs/`](specs/) | 当前有效或接近冻结的实现规格 |
| [`decisions/`](decisions/) | 已接受的架构决策，类似 ADR |
| [`archive/`](archive/) | 历史讨论、被替代方案和归档草稿 |

## UX 与任务文档

| 文档 | 说明 |
|---|---|
| [`ux.md`](ux.md) | 页面体验、视觉要求、交互标准 |
| [`ui-audit.md`](ui-audit.md) | UI 审计和体验问题清单 |
| [`product-backlog.md`](product-backlog.md) | 长期产品需求池 |
| [`operation-backlog.md`](operation-backlog.md) | 长期运维需求池 |
| [`roadmap.md`](roadmap.md) | MVP 与后续迭代计划 |
| [`long-term-roadmap.md`](long-term-roadmap.md) | 当前状态、长期业务定位、模型演进和未来阶段规划 |
| [`task-board.md`](task-board.md) | 当前执行看板、任务状态、完成标识 |
| [`tasks/`](tasks/) | 复杂任务详情页 |

## 文档维护规则

1. README 只放项目入口、快速启动、核心图和文档索引。
2. 用户怎么用，写到 `user-guide.md`。
3. 功能是否可用，写到 `feature-matrix.md`。
4. 数据源和真实数据策略，写到 `data-sources.md` 和 `data-pipeline.md`。
5. 系统限制集中写到 `limitations.md`，不要分散在页面文案里。
6. API 能力和接口边界写到 `api.md`。
7. 生产排障写到 `operations-runbook.md`，发布检查写到 `release-checklist.md`。
8. 当前可实现规格写到 `docs/specs/`，长期方向写到 `docs/strategy/`。
9. 已接受的关键判断写到 `docs/decisions/`，每篇只记录一个决定、取舍和后果。
10. 历史讨论和被替代方案写到 `docs/archive/`，不得作为当前实现依据。
11. 历史任务文档只记录当时决策；当前运行策略以 `data-pipeline.md`、`data-sources.md` 和 `docs/specs/` 为准。
