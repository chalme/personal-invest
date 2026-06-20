# Task Board

本文档是当前执行看板，只放已经确认要推进的任务。长期想法仍放在
`docs/product-backlog.md` 和 `docs/operation-backlog.md`，复杂任务再拆到
`docs/tasks/*.md`。

## Current Mainline

当前主线：

1. 可用性：确保页面按钮、API、每日任务和线上访问真实可用。
2. 数据可信度：明确真实数据、样本数据、数据日期和数据来源。
3. 股票 + 基金双资产：股票和基金都要能进入观察、分析、持仓、信号和复盘。
4. 个人持仓 + 分级建议：持仓要能解释组合暴露，建议要由规则生成、可追溯，并用具象话说明原因。
5. 市场 + 行业全景：市场分析要覆盖热门、冷门、轮动、防守、过热行业，并映射到股票、ETF、基金。

## Status

| Status | Meaning |
|---|---|
| `TODO` | 已确认要做，尚未开始 |
| `IN_PROGRESS` | 正在做 |
| `DONE` | 已完成，并已写入完成标识 |
| `BLOCKED` | 被外部条件或产品决策阻塞 |

## Task Flow

1. 新想法先进入 backlog。
2. 确认要做后进入本文件，状态为 `TODO`。
3. 开始做时改成 `IN_PROGRESS`。
4. 任务较复杂时创建 `docs/tasks/{task-id}-{slug}.md`，并在本文件链接过去。
5. 做完后改成 `DONE`，写入 `Completed At`、`Changed Files`、`Verification`、`Notes`。

## Current Tasks

### P0-001: 修正每日任务按钮只入队不执行

- Status: `DONE`
- Priority: `P0`
- Goal: Dashboard 点击“执行今日更新”后，真正启动每日流水线，而不是只创建 `QUEUED` 任务记录。
- Files: `backend/app/api/jobs.py`, `backend/app/services/job_service.py`, `worker/daily_job.py`, `frontend/src/pages/Dashboard.tsx`
- Concrete Changes: 后端启动后台任务；任务状态可查询；前端轮询进度并在成功或失败后刷新状态。
- Acceptance: 点击按钮后任务从 `RUNNING` 进入 `SUCCESS` 或 `FAILED`，失败时页面展示错误原因。
- Completed At: 2026-06-20
- Changed Files: `backend/app/api/jobs.py`, `backend/app/services/job_service.py`, `worker/daily_job.py`, `frontend/src/pages/Dashboard.tsx`
- Verification: Dashboard 按钮会启动后台任务，任务状态可轮询至 `SUCCESS` 或 `FAILED`。
- Notes: 后端复用同一个 `job_execution.id` 更新任务进度。

### P0-002: 增加数据来源与样本数据提示

- Status: `DONE`
- Priority: `P0`
- Goal: 用户能清楚知道当前分析使用真实数据、样本数据，还是两者混用。
- Files: `worker/ingest/market_data.py`, `backend/app/api/market.py` 或新增 `backend/app/api/data.py`, `frontend/src/pages/Dashboard.tsx`, `frontend/src/pages/MarketPage.tsx`
- Concrete Changes: 暴露 `source_count`、`latest_trade_date`、`has_sample_data`；页面显示数据来源和风险提示。
- Acceptance: 使用样本数据时，Dashboard 和市场页有明确提示，系统不会把样本数据伪装成真实数据。
- Completed At: 2026-06-20
- Changed Files: `worker/ingest/market_data.py`, `backend/app/services/data_source_service.py`, `backend/app/api/market.py`, `backend/app/services/dashboard_service.py`, `frontend/src/pages/Dashboard.tsx`, `frontend/src/pages/MarketPage.tsx`
- Verification: Dashboard 和市场页会展示真实/样本/混合数据提示；后端提供 `GET /api/market/data-source`。
- Notes: 样本数据不会再被页面伪装成真实数据。

### P0-003: 引入资产类型字段

- Status: `DONE`
- Priority: `P0`
- Goal: 让股票、场内 ETF/LOF、场外基金在系统内有明确资产类型。
- Files: `backend/migrations/001_init.sql`, `scripts/init_db.py`, `backend/app/services/watchlist_service.py`, `backend/app/services/portfolio_service.py`, `frontend/src/api/types.ts`
- Concrete Changes: 引入 `asset_type` 概念；旧数据可按代码推断；自选、持仓、信号都返回资产类型。
- Acceptance: 股票、ETF、基金能在观察池和持仓中被区分展示。
- Completed At: 2026-06-20
- Changed Files: `backend/migrations/001_init.sql`, `scripts/init_db.py`, `backend/app/core/asset_type.py`, `backend/app/services/watchlist_service.py`, `backend/app/services/portfolio_service.py`, `worker/strategy/signal_engine.py`, `frontend/src/pages/WatchlistPage.tsx`, `frontend/src/pages/PortfolioPage.tsx`, `frontend/src/pages/SignalsPage.tsx`
- Verification: 初始化、daily job、后端编译、前端构建和 `make check` 通过。
- Notes: 详情见 `docs/tasks/P0-003-asset-type.md`。

### P0-004: 个人持仓与分级建议底座

- Status: `TODO`
- Priority: `P0`
- Goal: 让系统支持默认个人组合，并为股票、ETF、场外基金生成可追溯的分级买卖建议。
- Files: `backend/migrations/001_init.sql`, `scripts/init_db.py`, `backend/app/services/portfolio_service.py`, `worker/strategy/signal_engine.py`, `backend/app/services/ai_service.py`, `frontend/src/api/types.ts`
- Concrete Changes: 明确单组合持仓口径；新增建议等级；建议结果包含一句话结论、触发原因、关键指标、风险说明、复核动作、置信度和数据日期；AI 只解释规则生成的建议。
- Acceptance: 持仓页能区分观察资产和真实持仓；股票、ETF、基金能展示 `继续观察`、`买入关注`、`持有`、`减仓关注`、`卖出关注` 等建议等级，并用具象话说明为什么今天需要关注。
- Detail: 后续开始执行时拆到 `docs/tasks/P0-004-holdings-advice.md`。

### P1-007: 市场与行业全景分析

- Status: `TODO`
- Priority: `P1`
- Goal: 市场分析不只展示市场分数和少数强势行业，而是覆盖热门、冷门、轮动、防守、过热行业，并映射到股票、ETF、基金观察对象。
- Files: `worker/factor/market_trend.py`, `backend/app/services/market_service.py`, `backend/app/services/dashboard_service.py`, `frontend/src/pages/MarketPage.tsx`, `frontend/src/pages/SectorsPage.tsx`, `frontend/src/pages/Dashboard.tsx`
- Concrete Changes: 增加行业分组、完整强弱排名、行业变化解释、行业到观察资产的映射；Dashboard 展示摘要，行业页展示完整分析。
- Acceptance: 用户能看到市场里哪些方向热、哪些方向冷、哪些方向正在轮动，以及这些方向对应哪些股票、ETF 或基金。
- Detail: 暂不拆分。

### P1-001: 新增基金数据管线

- Status: `DONE`
- Priority: `P1`
- Goal: 基金第一版支持场外公募基金净值数据，同时兼容场内 ETF/LOF 的行情口径。
- Files: `worker/ingest/market_data.py`, `worker/daily_job.py`, `worker/storage.py`
- Concrete Changes: ETF 继续写入 `daily_bar`；场外基金新增 `fund_nav` 数据集；记录净值日期、数据来源和样本标识。
- Acceptance: 每日任务能产出股票/ETF 日线和基金净值数据。
- Completed At: 2026-06-20
- Changed Files: `worker/ingest/market_data.py`, `worker/daily_job.py`
- Verification: daily job 和 `make check` 通过；无基金时任务会跳过基金净值同步。
- Notes: 基金净值同步逻辑合并在 `worker/ingest/market_data.py`，详情见 `docs/tasks/P1-001-fund-data-pipeline.md`。

### P1-002: 新增基金分析快照

- Status: `DONE`
- Priority: `P1`
- Goal: 基金不套用股票基本面/估值评分，而使用收益、回撤、波动、类型适配等口径。
- Files: `backend/migrations/001_init.sql`, `worker/factor/fund_analysis.py`, `worker/daily_job.py`
- Concrete Changes: 新增 `fund_analysis_snapshot`；计算收益表现、回撤风险、波动、趋势、综合评分、结论和风险说明。
- Acceptance: 基金分析结果可独立生成，并能解释评分来源。
- Completed At: 2026-06-20
- Changed Files: `backend/migrations/001_init.sql`, `worker/factor/fund_analysis.py`, `worker/daily_job.py`
- Verification: 初始化、daily job、后端编译、前端构建和 `make check` 通过。
- Notes: 详情见 `docs/tasks/P1-002-fund-analysis.md`。

### P1-003: 新增基金分析 API 和页面

- Status: `DONE`
- Priority: `P1`
- Goal: 前端新增独立基金分析页，与个股分析页并列。
- Files: `backend/app/api/funds.py`, `backend/app/services/fund_service.py`, `backend/app/main.py`, `frontend/src/pages/FundsPage.tsx`, `frontend/src/components/layout/AppLayout.tsx`, `frontend/src/App.tsx`
- Concrete Changes: 新增基金分析接口和净值趋势接口；前端展示基金评分、净值曲线、回撤风险和分析结论。
- Acceptance: 用户能在基金分析页查看基金研究结论。
- Completed At: 2026-06-20
- Changed Files: `backend/app/api/funds.py`, `backend/app/services/fund_service.py`, `backend/app/main.py`, `frontend/src/pages/FundsPage.tsx`, `frontend/src/components/layout/AppLayout.tsx`, `frontend/src/App.tsx`, `frontend/src/api/types.ts`
- Verification: 初始化、daily job、后端编译、前端构建和 `make check` 通过。
- Notes: 详情见 `docs/tasks/P1-003-fund-page.md`。

### P1-004: 观察池支持股票和基金

- Status: `DONE`
- Priority: `P1`
- Goal: 自选股页升级为观察池，支持股票、ETF、场外基金。
- Files: `frontend/src/pages/WatchlistPage.tsx`, `backend/app/api/watchlist.py`, `backend/app/services/watchlist_service.py`
- Concrete Changes: 新增资产类型选择和筛选；文案从“自选股”调整为“观察池”。
- Acceptance: 用户能添加基金代码，并被基金分析页识别。
- Completed At: 2026-06-20
- Changed Files: `backend/app/api/watchlist.py`, `backend/app/services/watchlist_service.py`, `frontend/src/pages/WatchlistPage.tsx`, `frontend/src/components/layout/AppLayout.tsx`, `frontend/src/styles/global.css`
- Verification: 后端编译、前端构建和 `make check` 通过。
- Notes: 详情见 `docs/tasks/P1-004-observation-pool.md`。

### P1-005: 持仓页支持基金

- Status: `DONE`
- Priority: `P1`
- Goal: 股票和基金都能进入组合持仓与风险总览。
- Files: `frontend/src/pages/PortfolioPage.tsx`, `backend/app/services/portfolio_service.py`, `worker/risk/risk_engine.py`
- Concrete Changes: 持仓表展示资产类型；基金按份额、成本净值、当前净值计算；风险检查区分股票仓位风险和基金回撤/集中风险。
- Acceptance: 基金持仓能正确显示市值、盈亏和风险。
- Completed At: 2026-06-20
- Changed Files: `backend/app/services/portfolio_service.py`, `worker/risk/risk_engine.py`, `frontend/src/pages/PortfolioPage.tsx`, `frontend/src/api/types.ts`
- Verification: 初始化、daily job、后端编译、前端构建和 `make check` 通过。
- Notes: 详情见 `docs/tasks/P1-005-fund-portfolio.md`。

### P1-006: 信号、日报、AI 同时覆盖股票、基金和分级建议

- Status: `DONE`
- Priority: `P1`
- Goal: 报告和 AI 不再只解释个股，基金有独立结论、风险边界和分级建议解释。
- Files: `worker/strategy/signal_engine.py`, `worker/report/report_builder.py`, `backend/app/services/ai_service.py`, `frontend/src/pages/SignalsPage.tsx`, `frontend/src/pages/ReportsPage.tsx`, `frontend/src/pages/AiAnalysisPage.tsx`
- Concrete Changes: 股票信号和基金信号使用不同解释模板；日报增加基金观察区和资产建议区；AI 支持解释规则生成的分级建议。
- Acceptance: 信号、日报、AI 输出能区分股票、ETF、场外基金，并展示建议等级、依据、风险和数据日期。
- Completed At: 2026-06-20
- Changed Files: `worker/strategy/signal_engine.py`, `worker/report/report_builder.py`, `backend/app/services/ai_service.py`, `backend/app/api/ai.py`, `frontend/src/pages/AiAnalysisPage.tsx`
- Verification: 初始化、daily job、后端编译、前端构建和 `make check` 通过。
- Notes: 详情见 `docs/tasks/P1-006-fund-signals-reports-ai.md`。

## Completed Tasks

### DOC-003: 业务规划加入个人持仓与分级买卖建议

- Status: `DONE`
- Priority: `P0`
- Goal: 将系统业务主线明确为观察资产、个人持仓、组合复盘和分级买卖建议。
- Completed At: 2026-06-20
- Changed Files: `docs/business-roadmap.md`, `docs/business-information-architecture.md`, `docs/product-backlog.md`, `docs/purpose.md`, `docs/architecture.md`, `docs/ux.md`, `docs/README.md`, `docs/task-board.md`
- Verification: 文档明确回答系统给分级买卖建议、规则生成建议、AI 解释建议、不做自动交易、观察池和持仓不同、建议必须可追溯。
- Notes: 本任务只更新文档，不实现代码、数据库或 UI。

### DOC-002: 业务与信息架构说明

- Status: `DONE`
- Priority: `P0`
- Goal: 明确股票、ETF、场外基金在系统中的区别、数据口径、页面入口、报告口径和风险边界。
- Completed At: 2026-06-20
- Changed Files: `docs/business-information-architecture.md`, `docs/README.md`, `docs/purpose.md`, `docs/architecture.md`, `docs/task-board.md`
- Verification: 文档明确回答基金是否算股票、ETF 使用哪个分析口径、场外基金如何分析、持仓页如何解释基金风险。
- Notes: 本任务只更新文档，不实现代码、数据库或 UI。

### DOC-001: 建立任务分层文档

- Status: `DONE`
- Priority: `P0`
- Goal: 建立轻量三层任务治理结构：长期 backlog、当前 task board、复杂任务详情页。
- Completed At: 2026-06-20
- Changed Files: `docs/task-board.md`, `docs/tasks/README.md`, `docs/README.md`, `docs/product-backlog.md`, `docs/architecture.md`, `docs/purpose.md`
- Verification: 文档结构已创建，任务状态、任务流和完成标识规则已写入。
- Notes: 本任务只更新文档，不实现业务代码。

## Blocked Tasks

当前没有阻塞任务。

## Task Detail Index

复杂任务开始执行时再创建详情页。当前预留：

- `docs/tasks/P0-003-asset-type.md`
- `docs/tasks/P0-004-holdings-advice.md`
- `docs/tasks/P1-001-fund-data-pipeline.md`
- `docs/tasks/P1-002-fund-analysis.md`
- `docs/tasks/P1-003-fund-page.md`
