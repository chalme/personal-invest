# Task Board

本文档是当前执行看板，只放已经确认要推进的任务。长期想法仍放在
`docs/product-backlog.md` 和 `docs/operation-backlog.md`，复杂任务再拆到
`docs/tasks/*.md`。

## Current Mainline

当前主线：

1. 人工验收与生产权限事项单独跟踪，不作为 Code Agent 可独立完成任务。
2. Code Agent 当前优先收敛任务状态、数据可信度边界和服务器长期运行基础能力。
3. 真实数据源增强和关键页面结论化先进入拆解规划，不直接开启大范围开发。

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

## Human Track

以下任务需要真实浏览器、生产域名、Cloudflare、服务器或敏感配置权限，不能由 Code Agent 独立完成。

### MANUAL-001: 线上功能人工回归验收

- Status: `TODO`
- Priority: `P1`
- Owner: `Human`
- Goal: 使用真实浏览器和线上域名确认 Dashboard、Settings、股票页、基金 / ETF 页面、复盘页、运行时配置、CORS 和数据可信度展示均可用。
- Details: `docs/tasks/MANUAL-001-production-regression-checklist.md`
- Code Agent Boundary: 不作为开发任务自动执行；验收结果如发现缺陷，再单独拆 BUG 任务。
- Acceptance: 人工确认核心页面、API 请求和关键交互在生产环境正常。

### H-002: Cloudflare Access 配置

- Status: `TODO`
- Priority: `P0`
- Owner: `Human`
- Goal: 为 `invest.chalme.indevs.in` 和 `api.chalme.indevs.in` 增加访问保护，避免个人投资数据公网裸露。
- Files: `docs/operation-backlog.md`
- Code Agent Boundary: 可提供文档、检查清单和健康检查脚本；不能代替 Cloudflare 账号内的配置动作。
- Acceptance: 未登录访问前端和 API 被 Access 拦截；授权登录后页面和 API 正常。

### H-003: 源站端口与服务器防火墙确认

- Status: `TODO`
- Priority: `P0`
- Owner: `Human`
- Goal: 确认后端端口、前端端口和服务器 IP 不能绕过 Cloudflare Access 直接访问投资系统。
- Files: `docs/operation-backlog.md`
- Code Agent Boundary: 可提供防火墙建议和检查命令；不能直接操作服务器安全组或防火墙。
- Acceptance: 直接访问服务器 IP 和后端端口不能绕过访问保护；`/health` 不泄露敏感配置。

### H-004: 生产 Secret 与敏感配置确认

- Status: `TODO`
- Priority: `P1`
- Owner: `Human`
- Goal: 确认 `.env.server`、API key、生产路径、Cloudflare 配置和备份文件没有误提交或泄露。
- Code Agent Boundary: 可提供检查清单；不能读取或判断外部账号内的敏感配置。
- Acceptance: 敏感配置不进 Git、不出现在公开日志、不被健康检查接口暴露。

### H-005: 备份目标与恢复策略确认

- Status: `TODO`
- Priority: `P1`
- Owner: `Human`
- Goal: 决定备份保存位置、保留周期、是否压缩、是否加密、是否需要异地备份和恢复覆盖策略。
- Code Agent Boundary: 可实现本地备份脚本；备份介质和保留策略需要人工决策。
- Acceptance: 明确第一版备份策略，供 `OPS-002` 实现。

### H-006: 真实数据源选择与授权

- Status: `TODO`
- Priority: `P2`
- Owner: `Human`
- Goal: 决定后续真实数据源增强使用 AKShare 还是补充其他来源，并明确 API key、使用限制、付费和合规边界。
- Code Agent Boundary: 可拆技术任务；不能替代数据源授权、账号注册和成本决策。
- Acceptance: 明确下一阶段优先接入的数据源和可接受的 fallback 策略。

## Current Code Agent Tasks

以下任务不依赖人工验收或外部账号权限，可以由 Code Agent 独立推进。执行完成后需写入完成标识、检查结果和提交记录。

### DOC-005: 清理 task-board 当前主线与重复 DONE 任务块

- Status: `DONE`
- Priority: `P1`
- Owner: `Codex`
- Goal: 清理 `docs/task-board.md` 中已完成但仍影响判断的历史状态，让当前主线、人工任务、Code Agent 任务和 backlog 边界清晰。
- Files: `docs/task-board.md`, `docs/product-backlog.md`, `docs/long-term-roadmap.md`
- Scope: 更新 `Current Mainline`；明确 `P2-017` 已完成；明确 `MANUAL-001` 由 Human 单独验收；清理重复 DONE 任务块；把下一阶段候选任务指向 backlog / operation backlog。
- Out of Scope: 不改业务代码；不改前端；不改后端；不新增功能。
- Acceptance: `Current Mainline` 不再包含已完成任务；同一批 DONE 任务不重复出现；当前可开发任务、人工任务、backlog 任务边界清晰。
- Completed At: 2026-06-21
- Changed Files: `docs/task-board.md`, `docs/operation-backlog.md`
- Verification: `git diff --check`; 确认 Human Track 与 Current Code Agent Tasks 分区清晰；确认人工任务保留 TODO 且不自动执行。
- Notes: 本任务只收敛任务边界，不修改业务代码。

### BUG-001: 修正 fund_nav 可信度来源判断

- Status: `DONE`
- Priority: `P1`
- Owner: `Codex`
- Goal: 避免基金净值 `fund_nav` 只要存在 parquet 文件就被标记为 `REAL`，确保样本基金净值不会误导数据可信度总览。
- Files: `backend/app/services/data_credibility_service.py`, `worker/ingest/market_data.py`, `data/raw/fund/*_manifest.json`
- Scope: 读取最新 fund manifest；根据 `source_count.akshare` 和 `source_count.sample` 推导 `REAL` / `SAMPLE` / `MIXED` / `MISSING`；保持 Dashboard / Settings 展示结构不变。
- Out of Scope: 不接入新基金数据源；不改 parquet 格式；不重写基金分析；不改建议规则。
- Acceptance: 全样本基金净值显示 `SAMPLE`；混合来源显示 `MIXED`；无基金净值显示 `MISSING`；说明文案符合可信度边界。
- Completed At: 2026-06-21
- Changed Files: `backend/app/services/data_credibility_service.py`, `docs/task-board.md`
- Verification: `PYTHONPATH=backend uv run python` smoke test confirmed current fund_nav is `MISSING`; `uv run python -m compileall backend/app`; `git diff --check`.
- Notes: 第一版读取最新 `data/raw/fund/*_manifest.json` 的 `source_count` 推导可信度，不改变 parquet 格式或基金分析逻辑。

### OPS-DOC-001: 生产部署边界文档

- Status: `DONE`
- Priority: `P1`
- Owner: `Codex`
- Goal: 把当前生产部署边界文档化，为 Cloudflare Access、源站保护和健康检查提供执行依据。
- Files: `docs/operation-backlog.md`, `docs/development.md`, `README.md`
- Scope: 描述前端、后端、域名、端口关系；描述 Cloudflare Access 推荐边界；描述源站不能裸露的原因；描述 `/health` 和 `/health/cors` 的使用方式；增加人工配置清单。
- Out of Scope: 不配置 Cloudflare；不改服务器安全组；不实现应用内登录。
- Acceptance: 人工可以按文档完成 Access 配置和源站边界检查；哪些步骤需要人工、哪些可以脚本化边界清晰。
- Completed At: 2026-06-21
- Changed Files: `docs/development.md`, `docs/operation-backlog.md`, `README.md`, `docs/task-board.md`
- Verification: `git diff --check`; 文档明确前端/API 都需 Access 保护、源站不能裸露、健康检查与人工验收边界。
- Notes: 只写文档，不配置 Cloudflare、不改服务器安全组。

### OPS-002: 本地备份脚本任务

- Status: `DONE`
- Priority: `P1`
- Owner: `Codex`
- Goal: 提供一条命令备份 SQLite、Parquet、报告和配置，降低单机数据丢失风险。
- Files: `scripts/backup.sh`, `Makefile`, `.gitignore`, `docs/operation-backlog.md`
- Scope: 备份 `storage/invest.db`、`data/parquet/`、`reports/`、`config.yaml`；默认输出到 `backups/YYYYMMDD-HHMMSS/`；避免备份文件进入 Git。
- Out of Scope: 不接云存储；不做自动定时；不做加密第一版；不做恢复 UI。
- Acceptance: 一条命令生成完整备份目录；重复执行不覆盖旧备份；备份目录默认不入库。
- Completed At: 2026-06-21
- Changed Files: `scripts/backup.sh`, `Makefile`, `.gitignore`, `docs/operation-backlog.md`, `docs/task-board.md`
- Verification: `bash -n scripts/backup.sh`; `BACKUP_ROOT=/tmp/personal-invest-backup-test ./scripts/backup.sh`; `git diff --check`.
- Notes: `.env.server` 默认不备份，避免密钥误复制；备份目标、加密和异地策略仍由 `H-005` 人工确认。

### DATA-001: 统一数据源 manifest 可信度口径

- Status: `DONE`
- Priority: `P1`
- Owner: `Codex`
- Goal: 统一 market、fund 和后续真实数据源 manifest 的字段与 source mode 推导规则，避免可信度服务持续堆特殊分支。
- Files: `backend/app/services/data_credibility_service.py`, `worker/ingest/market_data.py`, `docs/data-pipeline.md`
- Scope: 设计统一 manifest 最小结构：`dataset`、`generated_at`、`latest_data_date`、`rows`、`asset_count`、`source_count`、`source_mode`、`warning`；兼容旧 manifest；提供统一推导函数。
- Out of Scope: 不重跑历史数据；不迁移旧 manifest；不接入新数据源；不做供应商 UI。
- Acceptance: market / fund 可以复用同一套 source mode 推导规则；缺字段时不报错；后续真实数据源接入无需重复造判断逻辑。
- Completed At: 2026-06-21
- Changed Files: `worker/ingest/market_data.py`, `backend/app/services/data_credibility_service.py`, `docs/data-pipeline.md`, `docs/task-board.md`
- Verification: `uv run python -m compileall backend/app worker scripts`; `PYTHONPATH=backend uv run python` smoke confirmed market/fund manifest modes; `git diff --check`.
- Notes: 新 manifest 保留旧字段并新增 `dataset`、`latest_data_date`、`asset_count`、`source_mode`、`warning`；可信度服务优先读取 manifest source mode，缺失时按 `source_count` 推导。

### OPS-003: systemd 服务模板

- Status: `DONE`
- Priority: `P1`
- Owner: `Codex`
- Goal: 提供后端 / 前端长期运行所需的 systemd 模板和启停文档。
- Files: `deploy/systemd/`, `docs/operation-backlog.md`, `docs/development.md`
- Scope: 提供 `personal-invest-backend.service`、`personal-invest-frontend.service` 模板；说明工作目录、启动命令、环境变量、日志查看、重启方式和开机自启。
- Out of Scope: 不在生产机直接启用；不做 Docker；不做 K8s；不做多实例部署。
- Acceptance: 模板可由人工复制到 `/etc/systemd/system/`；服务支持异常重启；文档说明如何查看日志和状态；不包含硬编码敏感信息。
- Completed At: 2026-06-21
- Changed Files: `deploy/systemd/personal-invest-backend.service`, `deploy/systemd/personal-invest-frontend.service`, `docs/development.md`, `docs/operation-backlog.md`, `docs/task-board.md`
- Verification: `systemd-analyze verify` when available; `git diff --check`.
- Notes: 只提供模板和启停文档，不在生产机执行 `systemctl enable --now`。

### OPS-004: 生产健康检查脚本

- Status: `DONE`
- Priority: `P2`
- Owner: `Codex`
- Goal: 提供一条命令检查前端、后端、API、域名和 CORS 的基础状态。
- Files: `scripts/health.sh`, `Makefile`, `docs/operation-backlog.md`
- Scope: 检查 `/health`、`/health/cors`、`/api/dashboard`、`/api/data/credibility`、前端页面 HTTP 状态、API 域名 HTTP 状态。
- Out of Scope: 不替代人工验收；不做完整 E2E；不做性能压测；不接告警系统。
- Acceptance: 一条命令输出健康检查结果；失败时能区分前端、后端、CORS、数据可信度 API 问题；不打印敏感信息。
- Completed At: 2026-06-21
- Changed Files: `scripts/health.sh`, `Makefile`, `docs/operation-backlog.md`, `docs/task-board.md`
- Verification: `bash -n scripts/health.sh`; `git diff --check`.
- Notes: 新增 `make health` / `make health-server`；脚本只做自动 smoke check，不替代 `MANUAL-001` 人工验收。

### DATA-002: 真实数据源增强任务拆解

- Status: `DONE`
- Priority: `P2`
- Owner: `Codex`
- Goal: 把“真实数据源增强”拆成可独立开发的小任务，避免一次性做成大泥球。
- Files: `docs/product-backlog.md`, `docs/data-pipeline.md`, `docs/task-board.md`
- Scope: 拆解行情日线稳定性、交易日历、股票财报、估值、基金净值、基金画像、ETF 跟踪指数与折溢价等子任务；每个子任务明确输入、输出、source_mode、fallback、页面影响和建议规则影响。
- Out of Scope: 不一次性实现所有数据源；不引入付费源；不写供应商配置 UI；不承诺全覆盖。
- Acceptance: 每个数据源增强任务都可以独立开发；每个任务都有清晰边界和验收标准。
- Completed At: 2026-06-21
- Changed Files: `docs/tasks/DATA-002-real-data-source-enhancement-planning.md`, `docs/data-pipeline.md`, `docs/product-backlog.md`, `docs/task-board.md`
- Verification: `git diff --check`; 确认 DATA-003 到 DATA-010 均包含输入、输出、source_mode、fallback、页面影响和建议规则影响。
- Notes: 本任务只拆解，不接入新真实数据源。

### UX-001: 关键页面结论化打磨规划

- Status: `DONE`
- Priority: `P2`
- Owner: `Codex`
- Goal: 规划股票页、持仓页、观察池、日报如何从“数据展示”升级为“结论优先”。
- Files: `docs/ux.md`, `docs/product-backlog.md`, `docs/business-information-architecture.md`
- Scope: 规划股票页研究结论化、持仓页组合决策化、观察池研究状态化、日报投资简报化；明确数据可信度在页面中的展示位置。
- Out of Scope: 不直接重构页面；不新增复杂图表；不改设计系统；不用 AI 生成高置信建议。
- Acceptance: 每个页面明确首屏要回答的问题；每个页面区分事实、判断、风险、动作；明确低可信数据如何降级展示。
- Completed At: 2026-06-21
- Changed Files: `docs/tasks/UX-001-key-page-conclusion-planning.md`, `docs/ux.md`, `docs/product-backlog.md`, `docs/business-information-architecture.md`, `docs/task-board.md`
- Verification: `git diff --check`; 确认 UX-002 到 UX-005 均明确首屏问题、信息分类和低可信数据降级规则。
- Notes: 本任务只做规划，不直接重构页面。

## Completed / Historical Tasks

### DOC-004: 收敛产品 backlog 与长期路线图状态

- Status: `DONE`
- Priority: `P1`
- Goal: 将产品 backlog、长期路线图和任务看板与当前已实现能力对齐，避免已完成能力继续以未完成待办形式出现。
- Details: `docs/tasks/DOC-004-product-roadmap-state-alignment.md`
- Files: `docs/product-backlog.md`, `docs/long-term-roadmap.md`, `docs/task-board.md`, `docs/README.md`
- Concrete Changes: 更新已完成能力、当前真实短板和下一阶段方向；不改业务代码。
- Acceptance: 已完成能力不再被描述为当前未完成主线；当前短板只保留真实短板；下一阶段任务方向清晰；`git diff --check` 通过。
- Completed At: 2026-06-21
- Changed Files: `docs/product-backlog.md`, `docs/long-term-roadmap.md`, `docs/task-board.md`, `docs/tasks/DOC-004-product-roadmap-state-alignment.md`
- Verification: `git diff --check`; 确认 `long-term-roadmap` 当前短板不再列出已完成底座；确认 `product-backlog` 增加已完成能力快照和真实下一阶段主线。
- Notes: 文档状态收敛任务，不是线上人工验收，也不是新功能实现。

### P2-017: 数据可信度总览 V1

- Status: `DONE`
- Priority: `P2`
- Goal: 提供统一数据可信度总览，让用户知道各分析模块使用真实、估算、样本还是缺失数据。
- Details: `docs/tasks/P2-017-data-credibility-overview.md`
- Files: `backend/app/services/data_credibility_service.py`, `backend/app/api/`, `frontend/src/pages/Dashboard.tsx`, `frontend/src/pages/SettingsPage.tsx`, `frontend/src/api/types.ts`
- Concrete Changes: 新增数据可信度服务与 API；Dashboard 展示摘要；Settings 展示完整模块表；明确 `REAL` / `ESTIMATED` / `SAMPLE` / `MISSING` / `MIXED` 的建议边界。
- Acceptance: API 返回全局摘要和模块列表；Dashboard 与 Settings 能展示可信度；股票财报、场外基金深度、ETF 深度均被统计；无 FUND 时显示 MISSING；前端构建通过。
- Completed At: 2026-06-21
- Changed Files: `backend/app/services/data_credibility_service.py`, `backend/app/api/data.py`, `backend/app/main.py`, `frontend/src/api/types.ts`, `frontend/src/pages/Dashboard.tsx`, `frontend/src/pages/SettingsPage.tsx`, `docs/task-board.md`, `docs/tasks/P2-017-data-credibility-overview.md`
- Verification: `uv run python scripts/migrate_db.py`; `PYTHONPATH=backend uv run python` smoke tested `DataCredibilityService`; `uv run python -m compileall backend/app worker scripts`; `git diff --check`. Frontend build 未执行：当前环境缺少 `pnpm`。
- Notes: 只做数据可信度可见性，不在本任务接入真实数据源或重写建议规则。当前统计覆盖市场、行情日线、基金净值、股票财报、场外基金深度、ETF 深度、组合快照和复盘闭环。

### P1-016: 低摩擦决策复盘闭环验收

- Status: `DONE`
- Priority: `P1`
- Goal: 验证 P1-011 到 P1-015 的复盘闭环是否真的低打扰、可解释、可持续使用。
- Details: `docs/tasks/P1-016-review-loop-acceptance.md`
- Files: `backend/app/services/review_service.py`, `backend/app/api/review.py`, `frontend/src/pages/ReviewPage.tsx`, `frontend/src/pages/Dashboard.tsx`, `frontend/src/pages/PortfolioPage.tsx`, `worker/review/outcome_tracker.py`
- Concrete Changes: 执行验收并允许修复小型一致性、文案、状态流、空态问题；不新增表、不新增大页面、不改核心模型。
- Acceptance: `review_task` 去重、延后、解决、自动失效正确；`decision_record` 轻量可用且允许独立存在；`decision_outcome` 只做复盘参考；Dashboard 只展示摘要；ReviewPage 承担完整流程；Portfolio 只做入口。
- Completed At: 2026-06-21
- Changed Files: `frontend/src/pages/ReviewPage.tsx`, `docs/task-board.md`, `docs/tasks/P1-016-review-loop-acceptance.md`
- Verification: `uv run python scripts/migrate_db.py`; repeated `uv run python -m worker.review.task_generator`; `uv run python -m worker.review.outcome_tracker`; ReviewService overview smoke test; independent decision creation smoke test; `cd frontend && pnpm build`; `./scripts/check.sh`.
- Notes: 修复复盘页只能从重要事项记录决策的问题，新增“记录独立决策”入口；后续分析规划任务已在 `P2-003` / `P2-004` / `P2-005` 收口。

### P2-002: 桌面端主题与密度系统

- Status: `DONE`
- Priority: `P2`
- Goal: 优化桌面端使用体验，建立亮/暗主题、信息密度和视觉一致性基础，不做移动端响应式适配。
- Details: `docs/tasks/P2-002-desktop-theme-density.md`
- Files: `frontend/src/styles/global.css`, `frontend/src/pages/SettingsPage.tsx`, `frontend/src/components/layout/AppLayout.tsx`, `frontend/src/api/types.ts`
- Concrete Changes: 新增桌面端主题变量、亮/暗主题切换、标准/紧凑密度、卡片/表格/图表间距统一和设置持久化；不引入移动端导航、触摸优化或小屏重排。
- Acceptance: 桌面端 Dashboard、观察池、持仓、基金、股票、复盘等页面视觉层级一致；主题和密度设置可保存并生效；前端构建通过；移动端适配不在本任务范围内。
- Completed At: 2026-06-21
- Changed Files: `frontend/src/App.tsx`, `frontend/src/pages/SettingsPage.tsx`, `frontend/src/utils/uiPreferences.ts`, `frontend/src/styles/global.css`
- Verification: `uv run python -m compileall backend/app worker scripts`. Frontend build 未执行：当前环境缺少 `node/pnpm`。
- Notes: 原 `P2-002` 保留编号重定义为桌面端体验任务；移动端响应式后续另拆 `P2-016`。本任务只实现桌面端主题/密度，不改移动端布局。

### P2-003: 股票财报分析规划

- Status: `DONE`
- Priority: `P2`
- Goal: 为 `STOCK` 设计财报数据、财务指标、估值、财报事件和股票质量分析口径。
- Details: `docs/tasks/P2-003-stock-financial-analysis-planning.md`
- Files: `docs/tasks/P2-003-stock-financial-analysis-planning.md`, `docs/stock-financial-analysis-design.md`
- Concrete Changes: 输出设计文档，覆盖数据模型、数据来源、指标口径、估值口径、worker 流程、API 范围、页面范围、`review_task` 接入点、`risk_event` 接入点和 AI 解释边界。
- Acceptance: 规划明确该能力只适用于 `STOCK`；ETF、LOF、FUND 不使用股票财报、公司估值或公司质量评分；财报异常能进入风险、重要事项、日报和 AI 解释链路。
- Completed At: 2026-06-21
- Changed Files: `docs/stock-financial-analysis-design.md`, `docs/tasks/P2-003-stock-financial-analysis-planning.md`, `docs/task-board.md`, `docs/README.md`, `docs/long-term-roadmap.md`
- Verification: `rtk git diff --check`; 搜索确认股票财报设计文档存在并被文档索引引用；确认设计明确只适用于 `STOCK`。
- Notes: 本任务只完成设计规划，不实现代码；后续再拆股票财报分析 V1 实现任务。

### P2-004: 场外基金深度分析规划

- Status: `DONE`
- Priority: `P2`
- Goal: 为 `FUND` 设计基金画像、基金经理/公司、基准/同类比较、风险收益、风格稳定性和持有体验口径。
- Details: `docs/tasks/P2-004-fund-deep-analysis-planning.md`
- Files: `docs/tasks/P2-004-fund-deep-analysis-planning.md`, `docs/fund-deep-analysis-design.md`
- Concrete Changes: 输出设计文档，覆盖基金画像、基金经理/基金公司、基准比较、同类比较、风险收益、风格和持仓暴露、worker 流程、API 范围、页面范围、`review_task` 接入点和 AI 解释边界。
- Acceptance: 规划明确场外基金深度分析不套股票模型，也不混入 ETF 深度口径；FUND 看产品、经理、策略、风险收益、基准/同类比较和持有体验；基金异常能进入风险、重要事项、日报和 AI 解释链路。
- Completed At: 2026-06-21
- Changed Files: `docs/fund-deep-analysis-design.md`, `docs/tasks/P2-004-fund-deep-analysis-planning.md`, `docs/task-board.md`, `docs/README.md`, `docs/long-term-roadmap.md`
- Verification: `rtk git diff --check`; 搜索确认场外基金设计文档存在并被文档索引引用；确认 `P2-004` 聚焦 `FUND`，不混入 ETF 深度范围。
- Notes: 本任务只完成设计规划，不实现代码；后续再拆场外基金深度分析 V1 实现任务。

### P2-005: ETF 深度分析规划

- Status: `DONE`
- Priority: `P2`
- Goal: 为 `ETF` / `LOF` 单独设计指数、主题、流动性、跟踪质量、折溢价、规模、成交额和交易风险分析口径。
- Details: `docs/tasks/P2-005-etf-deep-analysis-planning.md`
- Files: `docs/tasks/P2-005-etf-deep-analysis-planning.md`, `docs/etf-deep-analysis-design.md`
- Concrete Changes: 输出设计文档，覆盖跟踪指数、主题/行业/地区/风格暴露、成交额、流动性、跟踪误差、折溢价、规模、交易风险、worker 流程、API 范围、页面范围、`review_task` 接入点和 AI 解释边界。
- Acceptance: 规划明确 ETF 不使用股票财报模型，也不混入场外基金经理/净值持有体验模型；ETF 继续保留现有 `ETF_PRICE` 基础分析，深度分析独立排期。
- Completed At: 2026-06-21
- Changed Files: `docs/etf-deep-analysis-design.md`, `docs/tasks/P2-005-etf-deep-analysis-planning.md`, `docs/task-board.md`, `docs/README.md`, `docs/long-term-roadmap.md`
- Verification: `rtk git diff --check`; 搜索确认 ETF 设计文档存在并被文档索引引用；确认 ETF 深度分析独立于股票财报和场外基金深度模型。
- Notes: 本任务只完成设计规划，不实现代码；实现优先级仍低于 `P2-003` 和 `P2-004` 对应的 V1 开发。

### P2-006: 股票财报数据层与快照

- Status: `DONE`
- Priority: `P2`
- Goal: 落地股票财报、财务指标、估值和公司质量快照的数据层与 worker 计算链路。
- Details: `docs/tasks/P2-006-stock-financial-data-layer.md`
- Files: `backend/migrations/`, `worker/`, `backend/app/services/`
- Concrete Changes: 新增 `financial_statement_snapshot`、`financial_metric_snapshot`、`valuation_snapshot`、`stock_quality_snapshot` 所需表结构和 worker；补齐 `source_mode`、`data_date`、`data_version` 等追溯字段。
- Acceptance: 股票财报快照能生成并区分真实、估算、样本和缺失数据；公司质量和估值输入可被后续 API 和建议链路读取。
- Completed At: 2026-06-21
- Changed Files: `backend/migrations/011_stock_financial_snapshots.sql`, `worker/factor/stock_financial.py`, `worker/daily_job.py`, `backend/app/services/stock_financial_service.py`
- Verification: `uv run python scripts/migrate_db.py`; `uv run python -m worker.factor.stock_financial`; queried four financial snapshot tables; `uv run python -m compileall backend/app worker scripts`; `./scripts/check.sh`.
- Notes: 只做数据层与计算，不在本任务完成页面和复盘接入；当前 SAMPLE / ESTIMATED 数据有明确 `source_mode`。

### P2-007: 股票财报 API 与页面接入

- Status: `DONE`
- Priority: `P2`
- Goal: 将股票财报、估值和公司质量快照接入后端 API 与股票分析页。
- Details: `docs/tasks/P2-007-stock-financial-api-page.md`
- Files: `backend/app/api/`, `backend/app/services/`, `frontend/src/pages/`
- Concrete Changes: 提供财报摘要、财务指标趋势、估值分位、公司质量摘要接口；在股票分析页展示公司质量、估值位置、核心指标趋势、数据来源和 AI 财报解释入口。
- Acceptance: 用户能在股票分析页看到财报和估值层信息；接口返回结构稳定；页面明确展示数据日期和来源。
- Completed At: 2026-06-21
- Changed Files: `backend/app/api/stocks.py`, `backend/app/services/stock_financial_service.py`, `frontend/src/pages/StocksPage.tsx`
- Verification: `PYTHONPATH=backend uv run python` smoke tested `StockFinancialService`; `cd frontend && pnpm build`; `./scripts/check.sh`.
- Notes: 股票页展示公司质量、估值、ROE、现金流、负债率和数据来源；不在本任务内落地财报异常到复盘闭环。

### P2-008: 股票财报事件与复盘闭链接入

- Status: `DONE`
- Priority: `P2`
- Goal: 让股票财报异常成为风险事件、重要事项、日报和 AI 解释输入。
- Details: `docs/tasks/P2-008-stock-financial-review-integration.md`
- Files: `worker/`, `backend/app/services/review_service.py`, `worker/report/`, `backend/app/services/ai_service.py`
- Concrete Changes: 新增 `financial_event` 识别逻辑；重要财报异常写入 `risk_event`、生成 `review_task`、进入日报和 AI 解释；按规则影响建议等级。
- Acceptance: 财报异常不会只停留在股票页面；重要变化会进入复盘闭环；AI 只解释规则和数据依据。
- Completed At: 2026-06-21
- Changed Files: `backend/migrations/012_financial_event.sql`, `worker/financial/events.py`, `worker/financial/__init__.py`, `worker/daily_job.py`, `backend/app/services/ai_service.py`
- Verification: `uv run python scripts/migrate_db.py`; `uv run python -m worker.financial.events`; `uv run python -m worker.review.task_generator`; queried `financial_event`, `risk_event`, and `review_task`; `uv run python -m compileall backend/app worker scripts`; `./scripts/check.sh`.
- Notes: 财报异常写入 `financial_event` 和 `risk_event`，并通过现有 review task 生成器进入复盘闭环；不新增自动交易或 AI 自由建议。

### P2-009: 场外基金画像与风险收益快照

- Status: `DONE`
- Priority: `P2`
- Goal: 落地场外基金画像、经理 / 公司信息和风险收益快照。
- Details: `docs/tasks/P2-009-fund-profile-risk-return.md`
- Files: `backend/migrations/`, `worker/`, `backend/app/services/`
- Concrete Changes: 新增 `fund_profile`、`fund_manager_profile`、`fund_company_profile`、`fund_risk_return_snapshot`；计算阶段收益、最大回撤、波动、夏普、卡玛和回撤修复时间。
- Acceptance: 场外基金基础画像和风险收益快照可生成并供后续页面、建议和复盘读取。
- Completed At: 2026-06-21
- Changed Files: `backend/migrations/013_fund_profile_risk_return.sql`, `worker/fund/deep_profile.py`, `worker/fund/__init__.py`, `worker/daily_job.py`, `backend/app/services/fund_deep_service.py`
- Verification: `uv run python scripts/migrate_db.py`; `uv run python -m worker.fund.deep_profile`; verified no active FUND assets are skipped without mixing ETF / LOF; `uv run python -m compileall backend/app worker scripts`; `./scripts/check.sh`.
- Notes: ETF / LOF 不混入本任务；当前无 active FUND 时安全跳过，用户加入 FUND 后自动生成画像和风险收益快照。

### P2-010: 场外基金基准 / 同类比较与暴露

- Status: `DONE`
- Priority: `P2`
- Goal: 落地场外基金的基准比较、同类比较和持仓暴露分析。
- Details: `docs/tasks/P2-010-fund-benchmark-peer-exposure.md`
- Files: `backend/migrations/`, `worker/`, `backend/app/services/`
- Concrete Changes: 新增 `fund_benchmark_snapshot`、`fund_peer_rank_snapshot`、`fund_holding_exposure_snapshot`；计算相对基准收益、同类排名 / 分位、风格和持仓暴露。
- Acceptance: 场外基金能解释是否跑赢基准、同类位置如何、是否与现有组合形成重复暴露。
- Completed At: 2026-06-21
- Changed Files: `backend/migrations/014_fund_benchmark_peer_exposure.sql`, `worker/fund/benchmark_peer.py`, `worker/daily_job.py`, `backend/app/services/fund_deep_service.py`
- Verification: `uv run python scripts/migrate_db.py`; `uv run python -m worker.fund.benchmark_peer`; verified no `fund_profile` rows are skipped without mixing ETF / LOF; `uv run python -m compileall backend/app worker scripts`; `./scripts/check.sh`.
- Notes: 先做场外基金，不推进 ETF 指数暴露和跟踪质量；当前无 fund_profile 时安全跳过。

### P2-011: 场外基金深度页与复盘闭链接入

- Status: `DONE`
- Priority: `P2`
- Goal: 将场外基金深度能力接入基金分析页、重要事项、日报和 AI 解释。
- Details: `docs/tasks/P2-011-fund-deep-page-review.md`
- Files: `backend/app/api/`, `backend/app/services/`, `frontend/src/pages/FundsPage.tsx`, `worker/report/`, `backend/app/services/ai_service.py`
- Concrete Changes: 在基金分析页增加基金画像、经理 / 公司、风险收益、基准 / 同类比较、风格暴露和持有体验模块；基金异常进入 `risk_event`、`review_task`、日报和 AI。
- Acceptance: 场外基金深度信息能被用户直接查看；重要异常会进入复盘闭环；AI 只解释规则和数据依据。
- Completed At: 2026-06-21
- Changed Files: `backend/migrations/015_fund_deep_event.sql`, `worker/fund/events.py`, `worker/daily_job.py`, `backend/app/api/funds.py`, `backend/app/services/ai_service.py`, `frontend/src/pages/FundsPage.tsx`
- Verification: `uv run python scripts/migrate_db.py`; `uv run python -m worker.fund.events`; `uv run python -m worker.review.task_generator`; `uv run python -m compileall backend/app worker scripts`; `cd frontend && pnpm build`; `./scripts/check.sh`.
- Notes: 本任务只针对 `FUND`，ETF 深度实现继续后置；基金页新增深度画像区块，基金深度异常通过 `risk_event` 进入复盘闭环。

### P2-012: ETF 画像与暴露数据层

- Status: `DONE`
- Priority: `P2`
- Goal: 为 ETF / LOF 建立独立画像与暴露数据层，补齐跟踪指数、主题、行业、地区、风格和资产类别暴露。
- Details: `docs/tasks/P2-012-etf-profile-exposure.md`
- Files: `backend/migrations/`, `worker/etf/`, `backend/app/services/etf_deep_service.py`, `worker/daily_job.py`
- Concrete Changes: 新增 ETF 画像和暴露快照表；从 `instrument` 与观察池回填 ETF/LOF；生成指数、主题、行业、地区、风格暴露；明确 `source_mode` 和 `data_version`。
- Acceptance: ETF 不进入股票财报模型，也不进入场外基金经理模型；ETF 能解释跟踪指数、主题和主要暴露；无真实暴露数据时明确标记估算或缺失，不伪装成真实数据。
- Completed At: 2026-06-21
- Changed Files: `backend/migrations/016_etf_profile_exposure.sql`, `worker/etf/profile_exposure.py`, `worker/etf/__init__.py`, `worker/daily_job.py`
- Verification: `uv run python scripts/migrate_db.py`; `uv run python -m worker.etf.profile_exposure`; 查询 `etf_profile` 和 `etf_exposure_snapshot`; `uv run python -m compileall backend/app worker scripts`. `./scripts/check.sh` 因当前执行环境缺少 `pnpm` 未能完成前端阶段。
- Notes: 这是 ETF 深度分析 V1 的数据底座，不接页面和复盘闭环；当前 ETF 暴露为 `ESTIMATED`，不会伪装为真实数据。

### P2-013: ETF 流动性与风险收益快照

- Status: `DONE`
- Priority: `P2`
- Goal: 为 ETF / LOF 生成流动性、阶段收益、回撤、波动和交易风险快照。
- Details: `docs/tasks/P2-013-etf-liquidity-risk-return.md`
- Files: `backend/migrations/`, `worker/etf/`, `backend/app/services/etf_deep_service.py`, `worker/daily_job.py`
- Concrete Changes: 新增 ETF 流动性和风险收益快照表；计算成交额、成交量、估算规模、阶段收益、最大回撤、波动和流动性风险等级；复杂盘口和实时价差后置。
- Acceptance: ETF 能解释交易是否足够活跃、回撤是否扩大、波动是否升高；缺失成交额或规模数据时不生成高置信度结论；不影响 `FUND` 深度分析。
- Completed At: 2026-06-21
- Changed Files: `backend/migrations/017_etf_liquidity_risk_return.sql`, `worker/etf/liquidity_risk_return.py`, `backend/app/services/etf_deep_service.py`, `worker/daily_job.py`
- Verification: `uv run python scripts/migrate_db.py`; `uv run python -m worker.etf.liquidity_risk_return`; 查询 `etf_liquidity_snapshot` 和 `etf_risk_return_snapshot`; `uv run python -m compileall backend/app worker scripts`. `./scripts/check.sh` 因当前执行环境缺少 `pnpm` 未能完成前端阶段。
- Notes: 第一版优先使用已有 `daily_bar` 和可得元数据，避免依赖难拿的实时盘口数据；当前样本数据来源标记为 `ESTIMATED`。

### P2-014: ETF 跟踪质量与折溢价

- Status: `DONE`
- Priority: `P2`
- Goal: 建立 ETF / LOF 跟踪误差、跟踪偏离、折溢价和指数拟合质量快照。
- Details: `docs/tasks/P2-014-etf-tracking-premium.md`
- Files: `backend/migrations/`, `worker/etf/`, `backend/app/services/etf_deep_service.py`, `worker/daily_job.py`
- Concrete Changes: 新增 ETF 跟踪质量快照；在可得指数/净值数据时计算跟踪误差、跟踪偏离、折溢价和拟合质量；数据不足时输出 `MISSING` / `ESTIMATED`。
- Acceptance: ETF 跟踪质量不会用假数据冒充真实指标；页面和 AI 能区分真实、估算和缺失；跟踪异常可供后续复盘闭链接入。
- Completed At: 2026-06-21
- Changed Files: `backend/migrations/018_etf_tracking_quality.sql`, `worker/etf/tracking_quality.py`, `backend/app/services/etf_deep_service.py`, `worker/daily_job.py`
- Verification: `uv run python scripts/migrate_db.py`; `uv run python -m worker.etf.tracking_quality`; 查询 `etf_tracking_snapshot`; `uv run python -m compileall backend/app worker scripts`. `./scripts/check.sh` 因当前执行环境缺少 `pnpm` 未能完成前端阶段。
- Notes: 跟踪质量对数据源依赖较强，本任务必须优先保证数据可信度和边界说明。

### P2-015: ETF 页面、AI 与复盘闭链接入

- Status: `DONE`
- Priority: `P2`
- Goal: 将 ETF 深度分析接入页面、AI、风险事件、重要事项和日报，形成 ETF 专项复盘闭环。
- Details: `docs/tasks/P2-015-etf-page-ai-review.md`
- Files: `backend/app/api/`, `backend/app/services/`, `frontend/src/pages/FundsPage.tsx`, `backend/app/services/ai_service.py`, `worker/report/`, `worker/review/`
- Concrete Changes: 提供 ETF 深度 API；在基金/ETF 页面展示 ETF 画像、暴露、流动性、风险收益、跟踪质量和折溢价；ETF 异常写入 `risk_event` 并进入 `review_task`、日报和 AI 解释。
- Acceptance: 用户能直接查看 ETF 专项深度信息；AI 明确按 ETF 模型解释，不套股票财报或场外基金经理模型；异常能进入复盘闭环但不制造每日待办压力。
- Completed At: 2026-06-21
- Changed Files: `backend/migrations/019_etf_deep_event.sql`, `worker/etf/events.py`, `worker/daily_job.py`, `backend/app/api/funds.py`, `backend/app/api/ai.py`, `backend/app/services/ai_service.py`, `backend/app/services/etf_deep_service.py`, `worker/report/report_builder.py`, `frontend/src/pages/FundsPage.tsx`
- Verification: `uv run python scripts/migrate_db.py`; `uv run python -m worker.etf.events`; `uv run python -m worker.review.task_generator`; ETF deep service smoke; `AIService().explain_etf`; `uv run python -m compileall backend/app worker scripts`. Frontend build 未执行：当前环境缺少 `node/pnpm`。
- Notes: ETF 深度接入完成后，股票、场外基金、ETF 三条深度分析线闭合。

### P1-011: Review Task 持久化

- Status: `DONE`
- Priority: `P1`
- Goal: 将当前只读重要事项聚合沉淀为 `review_task`，支持去重、状态、延后和自动失效。
- Details: `docs/tasks/P1-011-review-task-persistence.md`
- Files: `backend/migrations/008_review_task.sql`, `backend/app/services/review_service.py`, `backend/app/api/review.py`, `worker/review/task_generator.py`, `worker/daily_job.py`
- Concrete Changes: 新增 `review_task` 表；使用 `dedupe_key` 防重复；支持 `OPEN`、`ACKNOWLEDGED`、`SNOOZED`、`RESOLVED`、`AUTO_EXPIRED`；`NO_MAJOR_RISK` 不生成事项。
- Acceptance: 同一事项不会重复刷屏；延后事项默认不出现在 OPEN 列表；过期事项可自动失效；Dashboard 仍保持低打扰摘要。
- Completed At: 2026-06-21
- Changed Files: `backend/migrations/008_review_task.sql`, `backend/app/services/review_service.py`, `backend/app/api/review.py`, `worker/review/task_generator.py`, `worker/daily_job.py`
- Verification: `uv run python scripts/migrate_db.py`; repeated `uv run python -m worker.review.task_generator`; ReviewService task count / NO_MAJOR_RISK check; `uv run python -m compileall backend/app worker scripts`; `cd frontend && pnpm build`; `./scripts/check.sh`.
- Notes: UI 文案仍使用“重要事项 / 复核 / 延后 / 已解决”，避免把产品做成每日待办系统。

### P1-012: ReviewPage 接入持久化事项

- Status: `DONE`
- Priority: `P1`
- Goal: 让复盘页从实时聚合展示升级为持久化重要事项工作流。
- Details: `docs/tasks/P1-012-review-page-task-workflow.md`
- Files: `frontend/src/pages/ReviewPage.tsx`, `frontend/src/api/types.ts`, `frontend/src/styles/global.css`, `backend/app/api/review.py`
- Concrete Changes: 复盘页展示 `review_task`；支持确认、延后、解决；保留无重要事项空态；任务失败和数据异常仍明确提示。
- Acceptance: 用户可在复盘页处理重要事项；无重要事项时显示“暂无需要立即处理事项”；Dashboard 不承载完整处理流程。
- Completed At: 2026-06-21
- Changed Files: `frontend/src/pages/ReviewPage.tsx`, `frontend/src/api/types.ts`, `frontend/src/api/client.ts`, `frontend/src/styles/global.css`
- Verification: `cd frontend && pnpm build`; ReviewService update task status smoke test; `./scripts/check.sh`.
- Notes: 先让持久化事项体验跑通，再增加真实决策记录。

### P1-013: Decision Record

- Status: `DONE`
- Priority: `P1`
- Goal: 记录用户真实投资决策及原因，让系统能复盘“当时为什么这么做”。
- Details: `docs/tasks/P1-013-decision-record.md`
- Files: `backend/migrations/009_decision_record.sql`, `backend/app/services/review_service.py`, `backend/app/api/review.py`, `frontend/src/pages/ReviewPage.tsx`, `frontend/src/pages/PortfolioPage.tsx`
- Concrete Changes: 新增 `decision_record`；支持 `BUY`、`HOLD`、`REDUCE`、`SELL`、`NO_ACTION`；允许可选关联 `review_task` 和 `investment_advice`；记录原因、预期、信心和数据日期。
- Acceptance: 用户可以记录系统内外触发的真实决策；决策可以关联重要事项或建议，也可以独立存在；表单保持轻量。
- Completed At: 2026-06-21
- Changed Files: `backend/migrations/009_decision_record.sql`, `backend/app/services/review_service.py`, `backend/app/api/review.py`, `frontend/src/pages/ReviewPage.tsx`, `frontend/src/api/types.ts`, `frontend/src/styles/global.css`
- Verification: `uv run python scripts/migrate_db.py`; API smoke test created BUY/HOLD/REDUCE/SELL/NO_ACTION; `cd frontend && pnpm build`; `./scripts/check.sh`.
- Notes: 数据库使用英文枚举，前端展示中文。

### P1-014: Decision Outcome Tracking

- Status: `DONE`
- Priority: `P1`
- Goal: 自动跟踪决策后 1D / 1W / 1M 的轻量结果，用于复盘参考。
- Details: `docs/tasks/P1-014-decision-outcome-tracking.md`
- Files: `backend/migrations/010_decision_outcome.sql`, `worker/review/outcome_tracker.py`, `worker/daily_job.py`, `backend/app/api/review.py`
- Concrete Changes: 新增 `decision_outcome`；记录决策时和跟踪时的价格/净值、收益、建议等级和风险数量；daily job 自动刷新可到期的 outcome。
- Acceptance: 每个决策可沉淀 1D / 1W / 1M 结果；重复执行幂等；结果文案明确“仅供复盘参考，不代表决策绝对对错”。
- Completed At: 2026-06-21
- Changed Files: `backend/migrations/010_decision_outcome.sql`, `worker/review/outcome_tracker.py`, `worker/daily_job.py`, `backend/app/services/review_service.py`, `backend/app/api/review.py`
- Verification: `uv run python scripts/migrate_db.py`; repeated `uv run python -m worker.review.outcome_tracker`; smoke decision generated outcomes; Python compile; frontend build; `./scripts/check.sh`.
- Notes: 第一版不做复杂收益归因、交易成本归因或多账户评价。

### P1-015: 复盘摘要接入 Dashboard / Portfolio

- Status: `DONE`
- Priority: `P1`
- Goal: 将持久化重要事项、最近决策和 outcome 摘要接入首页与持仓页，但不把 Dashboard 做成任务处理页。
- Details: `docs/tasks/P1-015-review-summary-surfaces.md`
- Files: `backend/app/services/dashboard_service.py`, `backend/app/services/portfolio_service.py`, `frontend/src/pages/Dashboard.tsx`, `frontend/src/pages/PortfolioPage.tsx`
- Concrete Changes: Dashboard 展示 OPEN 重要事项数量、高优先级摘要和最近决策；Portfolio 页提供按资产记录决策和查看相关事项的入口；ReviewPage 仍是完整复盘主入口。
- Acceptance: 用户 30 秒内能知道是否需要介入；持仓页能进入记录决策；Dashboard 只显示摘要，不制造每日待办压力。
- Completed At: 2026-06-21
- Changed Files: `backend/app/services/review_service.py`, `frontend/src/pages/Dashboard.tsx`, `frontend/src/pages/ReviewPage.tsx`, `frontend/src/pages/PortfolioPage.tsx`, `frontend/src/api/types.ts`, `frontend/src/styles/global.css`
- Verification: ReviewService overview smoke test; `cd frontend && pnpm build`; `./scripts/check.sh`.
- Notes: 本任务是复盘闭环 V1 的收口任务。

### P1-010: 低摩擦投资工作台 V1

- Status: `DONE`
- Priority: `P1`
- Goal: 将系统从多页面数据展示升级为低摩擦决策工作台，打开首页即可知道今天是否需要介入。
- Details: `docs/tasks/P1-010-low-friction-workbench-v1.md`
- Files: `backend/app/services/review_service.py`, `backend/app/api/review.py`, `backend/app/services/dashboard_service.py`, `frontend/src/pages/Dashboard.tsx`, `frontend/src/pages/PortfolioPage.tsx`, `frontend/src/pages/ReviewPage.tsx`, `frontend/src/components/layout/AppLayout.tsx`, `frontend/src/styles/global.css`
- Concrete Changes: 聚合重要事项、修正 `NO_MAJOR_RISK` 语义、Dashboard 展示今日概览、复盘页展示建议变化和组合快照、持仓页增加复盘入口、文案从每日待办改为低摩擦提醒。
- Acceptance: 用户 30 秒内能知道今天是否需要介入；没有重要变化时显示“暂无需要立即处理事项”；系统不把用户做成每日打卡工具。
- Completed At: 2026-06-21
- Changed Files: `backend/app/api/review.py`, `backend/app/main.py`, `backend/app/services/review_service.py`, `backend/app/services/dashboard_service.py`, `frontend/src/App.tsx`, `frontend/src/api/types.ts`, `frontend/src/components/layout/AppLayout.tsx`, `frontend/src/pages/Dashboard.tsx`, `frontend/src/pages/PortfolioPage.tsx`, `frontend/src/pages/ReviewPage.tsx`, `frontend/src/styles/global.css`
- Verification: `uv run python scripts/init_db.py`; `PYTHONPATH=backend uv run python - <<'PY' ... ReviewService().overview() ... PY`; `cd frontend && pnpm build`; `./scripts/check.sh`。
- Notes: 第一版只做只读聚合，不新增 `review_task` 持久化；`NO_MAJOR_RISK` 已从重要事项池排除。

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

- Status: `DONE`
- Priority: `P0`
- Goal: 让系统支持默认个人组合，并为股票、ETF、场外基金生成可追溯的分级买卖建议。
- Files: `backend/migrations/001_init.sql`, `scripts/init_db.py`, `backend/app/services/portfolio_service.py`, `worker/strategy/signal_engine.py`, `backend/app/services/ai_service.py`, `frontend/src/api/types.ts`
- Concrete Changes: 明确单组合持仓口径；新增建议等级；建议结果包含一句话结论、触发原因、关键指标、风险说明、复核动作、置信度和数据日期；AI 只解释规则生成的建议。
- Acceptance: 持仓页能区分观察资产和真实持仓；股票、ETF、基金能展示 `继续观察`、`买入关注`、`持有`、`减仓关注`、`卖出关注` 等建议等级，并用具象话说明为什么今天需要关注。
- Completed At: 2026-06-20
- Changed Files: `backend/migrations/001_init.sql`, `scripts/init_db.py`, `worker/strategy/signal_engine.py`, `worker/daily_job.py`, `backend/app/services/portfolio_service.py`, `backend/app/services/ai_service.py`, `frontend/src/api/types.ts`, `frontend/src/pages/PortfolioPage.tsx`
- Verification: 初始化、daily job、SQLite 建议生成校验、前端构建和 `make check` 通过。
- Notes: 详情见 `docs/tasks/P0-004-holdings-advice.md`。

### P1-007: 市场与行业全景分析

- Status: `DONE`
- Priority: `P1`
- Goal: 市场分析不只展示市场分数和少数强势行业，而是覆盖热门、冷门、轮动、防守、过热行业，并映射到股票、ETF、基金观察对象。
- Files: `worker/factor/market_trend.py`, `backend/app/services/market_service.py`, `backend/app/services/dashboard_service.py`, `frontend/src/pages/MarketPage.tsx`, `frontend/src/pages/SectorsPage.tsx`, `frontend/src/pages/Dashboard.tsx`
- Concrete Changes: 增加行业分组、完整强弱排名、行业变化解释、行业到观察资产的映射；Dashboard 展示摘要，行业页展示完整分析。
- Acceptance: 用户能看到市场里哪些方向热、哪些方向冷、哪些方向正在轮动，以及这些方向对应哪些股票、ETF 或基金。
- Completed At: 2026-06-20
- Changed Files: `backend/app/services/market_service.py`, `backend/app/api/market.py`, `backend/app/services/dashboard_service.py`, `frontend/src/api/types.ts`, `frontend/src/pages/Dashboard.tsx`, `frontend/src/pages/SectorsPage.tsx`
- Verification: `uv run python worker/daily_job.py`、`uv run python` 调用 `MarketService().sector_panorama()` 验证输出结构、`./scripts/check.sh`
- Notes: 当前版本不新增行业全景表，直接基于最新 `sector_trend_snapshot` 和观察池映射实时生成，避免过早扩大数据模型。

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

## Next Phase: 模型收敛

### P0-005: 建立轻量迁移体系

- Status: `DONE`
- Priority: `P0`
- Goal: 建立可重复执行的数据库迁移机制，让后续新增表和字段不再混入 `001_init.sql` 或临时补列逻辑。
- Details: `docs/tasks/P0-005-schema-migration.md`
- Files: `backend/migrations/002_schema_migration.sql`, `scripts/migrate_db.py`, `scripts/init_db.py`
- Concrete Changes: 新增 `schema_migration(version, name, applied_at)`；新增迁移 runner；`init_db.py` 接入迁移；后续迁移使用稳定版本命名。
- Acceptance: 重复执行迁移幂等；迁移体系任务不混入业务字段；后续迁移可按 `003_instrument.sql` 这类文件顺序执行。
- Completed At: 2026-06-21
- Changed Files: `backend/migrations/002_schema_migration.sql`, `scripts/migrate_db.py`, `scripts/init_db.py`
- Verification: 重复执行 `uv run python scripts/init_db.py` 和 `uv run python scripts/migrate_db.py`，迁移表只记录 `001_init` 与 `002_schema_migration`，无重复应用。
- Notes: 本任务只建立迁移基础设施，没有引入业务模型字段。

### P0-006: 引入资产主数据 instrument

- Status: `DONE`
- Priority: `P0`
- Goal: 新增资产主数据表，统一股票、ETF、场外基金的名称、类型、市场、行业/主题基础信息和来源。
- Details: `docs/tasks/P0-006-instrument-master.md`
- Files: `backend/migrations/003_instrument.sql`, `scripts/init_db.py`, `backend/app/core/asset_type.py`
- Concrete Changes: 新增 `instrument` 表并包含 `source` 字段；从观察池、持仓、信号和建议回填资产；旧字段短期保留。
- Acceptance: `instrument` 能覆盖已有观察资产、持仓资产、信号资产和建议资产；读取路径逐步优先使用 `instrument`；资产类型归一走 `core.asset_type`。
- Completed At: 2026-06-21
- Changed Files: `backend/migrations/003_instrument.sql`, `backend/app/services/instrument_service.py`, `backend/app/services/watchlist_service.py`, `backend/app/services/portfolio_service.py`
- Verification: `make init`、重复迁移、SQLite 查询 `schema_migration` 与 `instrument` 回填结果通过。
- Notes: 旧表中的 `name` 和 `asset_type` 字段继续保留，读取路径优先使用 `instrument` 兜底旧字段。

### P0-007: 修正 ETF 独立分析口径

- Status: `DONE`
- Priority: `P0`
- Goal: 让 ETF 使用价格型分析口径，不再进入股票基本面、估值和公司质量分析路径。
- Details: `docs/tasks/P0-007-etf-analysis-type.md`
- Files: `backend/migrations/004_fund_analysis_type.sql`, `worker/factor/stock_analysis.py`, `worker/factor/fund_analysis.py`, `worker/strategy/signal_engine.py`
- Concrete Changes: `fund_analysis_snapshot` 增加 `analysis_type`；`FUND` 使用 `FUND_NAV`，`ETF` 使用 `ETF_PRICE`；基金页文案区分基金净值分析和 ETF 价格分析。
- Acceptance: ETF 不再新写入 `stock_analysis_snapshot`；ETF 信号和建议优先读取 `fund_analysis_snapshot where analysis_type = 'ETF_PRICE'`；页面能展示 ETF 分析来源。
- Completed At: 2026-06-21
- Changed Files: `backend/migrations/004_fund_analysis_type.sql`, `worker/factor/stock_analysis.py`, `worker/factor/fund_analysis.py`, `worker/strategy/signal_engine.py`, `worker/storage.py`, `backend/app/services/fund_service.py`, `frontend/src/api/types.ts`, `frontend/src/pages/FundsPage.tsx`
- Verification: 迁移应用、股票/基金分析函数执行通过，`./scripts/check.sh` 返回 `exit:0`。
- Notes: ETF 进入 `fund_analysis_snapshot` 的价格分析口径，股票分析和股票信号路径跳过非 STOCK 资产。

### P1-008: 拆分 advice_engine 并增加规则追溯

- Status: `DONE`
- Priority: `P1`
- Goal: 将投资建议生成从策略信号文件中拆出，并让每条建议能追溯规则版本、来源快照和变化原因。
- Details: `docs/tasks/P1-008-advice-engine-rule-trace.md`
- Files: `backend/migrations/005_advice_rule_trace.sql`, `worker/advice/`, `worker/strategy/signal_engine.py`, `worker/daily_job.py`
- Concrete Changes: 新增 advice 模块；`investment_advice` 增加规则追溯字段并预留 `rule_result`；保持原有建议结果尽量不变。
- Acceptance: 建议结果行为不大变；每条建议包含规则版本、来源快照、上一建议等级和变化原因；AI 和日报仍解释规则结果。
- Completed At: 2026-06-21
- Changed Files: `backend/migrations/005_advice_rule_trace.sql`, `worker/advice/__init__.py`, `worker/advice/engine.py`, `worker/strategy/signal_engine.py`, `worker/daily_job.py`
- Verification: 迁移应用、`generate_investment_advice()` 返回建议记录、`./scripts/check.sh` 通过。
- Notes: 建议规则结果迁入 `worker/advice`，策略信号文件只保留信号生成；建议表新增规则版本、来源快照、上一建议等级、变化原因和规则调试 JSON。

### P1-009: 新增资产行业/主题映射

- Status: `DONE`
- Priority: `P1`
- Goal: 建立资产到行业、主题、指数、地区和风格的正式暴露映射，替代单纯依赖 `watchlist.group_name` 的弱映射。
- Details: `docs/tasks/P1-009-instrument-sector-map.md`
- Files: `backend/migrations/006_instrument_sector_map.sql`, `backend/app/services/market_service.py`, `worker/factor/market_trend.py`
- Concrete Changes: 新增 `instrument_sector_map`；字段包含 `map_type`；行业全景优先读取映射表，无映射时 fallback 到 `watchlist.group_name`。
- Acceptance: 一个资产可以映射多个行业/主题；行业全景能用正式映射关联股票、ETF、基金；旧分组仍可兜底。
- Completed At: 2026-06-21
- Changed Files: `backend/migrations/006_instrument_sector_map.sql`, `backend/app/services/market_service.py`, `frontend/src/api/types.ts`
- Verification: 迁移应用、`MarketService().sector_panorama()` 返回正式映射资产、前端构建通过。
- Notes: 行业全景优先读取 `instrument_sector_map`，没有正式映射时继续 fallback 到 `watchlist.group_name`。

### P2-001: 新增组合历史快照

- Status: `DONE`
- Priority: `P2`
- Goal: 每日沉淀组合总览，支持组合曲线、风险变化、建议摘要和日报复盘。
- Details: `docs/tasks/P2-001-portfolio-snapshot.md`
- Files: `backend/migrations/007_portfolio_snapshot.sql`, `worker/daily_job.py`, `backend/app/services/portfolio_service.py`
- Concrete Changes: 新增 `portfolio_snapshot`；第一版只做日级总览，不做复杂归因、多账户或现金管理。
- Acceptance: 每日快照包含市值、成本、盈亏、股票/ETF/基金市值、集中度、风险数和建议摘要。
- Completed At: 2026-06-21
- Changed Files: `backend/migrations/007_portfolio_snapshot.sql`, `worker/portfolio/__init__.py`, `worker/portfolio/snapshot.py`, `worker/daily_job.py`, `backend/app/services/portfolio_service.py`
- Verification: 迁移应用、`build_portfolio_snapshot()` 生成 2026-06-19 快照、Python 编译和前端构建通过。
- Notes: 第一版只沉淀日级总览，不做现金、多账户、行业归因或收益归因。

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
- `docs/tasks/P1-007-market-sector-panorama.md`
- `docs/tasks/P0-005-schema-migration.md`
- `docs/tasks/P0-006-instrument-master.md`
- `docs/tasks/P0-007-etf-analysis-type.md`
- `docs/tasks/P1-008-advice-engine-rule-trace.md`
- `docs/tasks/P1-009-instrument-sector-map.md`
- `docs/tasks/P2-001-portfolio-snapshot.md`
- `docs/tasks/P1-010-low-friction-workbench-v1.md`
- `docs/tasks/P1-011-review-task-persistence.md`
- `docs/tasks/P1-012-review-page-task-workflow.md`
- `docs/tasks/P1-013-decision-record.md`
- `docs/tasks/P1-014-decision-outcome-tracking.md`
- `docs/tasks/P1-015-review-summary-surfaces.md`
- `docs/tasks/P1-016-review-loop-acceptance.md`
- `docs/tasks/P2-003-stock-financial-analysis-planning.md`
- `docs/tasks/P2-004-fund-deep-analysis-planning.md`
- `docs/tasks/P2-005-etf-deep-analysis-planning.md`
- `docs/tasks/P2-006-stock-financial-data-layer.md`
- `docs/tasks/P2-007-stock-financial-api-page.md`
- `docs/tasks/P2-008-stock-financial-review-integration.md`
- `docs/tasks/P2-002-desktop-theme-density.md`
- `docs/tasks/P2-009-fund-profile-risk-return.md`
- `docs/tasks/P2-010-fund-benchmark-peer-exposure.md`
- `docs/tasks/P2-011-fund-deep-page-review.md`
- `docs/tasks/P2-012-etf-profile-exposure.md`
- `docs/tasks/P2-013-etf-liquidity-risk-return.md`
- `docs/tasks/P2-014-etf-tracking-premium.md`
- `docs/tasks/P2-015-etf-page-ai-review.md`
- `docs/tasks/DOC-004-product-roadmap-state-alignment.md`
- `docs/tasks/P2-017-data-credibility-overview.md`
- `docs/tasks/MANUAL-001-production-regression-checklist.md`
- `docs/tasks/DATA-002-real-data-source-enhancement-planning.md`
- `docs/tasks/UX-001-key-page-conclusion-planning.md`
