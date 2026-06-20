# Personal Invest

浏览器可访问、页面优雅、体验良好的本地个人投资研究与复盘系统。

## 目标

系统围绕个人投资的完整闭环构建：

- 市场趋势判断
- 行业强弱判断
- 个股公司分析
- 自选股跟踪
- 持仓风险分析
- 策略信号生成
- 回测验证
- 投资日报/周报
- AI 辅助解释

系统只做研究、提醒、复盘和辅助判断，不做自动下单。

## 技术栈

- Backend: FastAPI
- Frontend: React + Vite + Tailwind + ECharts + TanStack Table
- Package Manager: uv + pnpm latest
- Storage: SQLite + DuckDB + Parquet
- Scheduler: APScheduler / 手动任务
- Reports: Markdown / HTML

## 前置依赖

需要本机安装：

```bash
uv --version
node --version
corepack --version
```

前端包管理器统一使用 Corepack 激活的最新稳定版 `pnpm`：

```bash
corepack enable
corepack prepare pnpm@latest --activate
pnpm --version
```

项目脚本会自动执行这一步。需要固定到某个版本时，可以用环境变量覆盖：

```bash
PNPM_VERSION=11 make dev
PNPM_VERSION=latest make dev
```

## 快速启动

一条命令启动前后端：

```bash
make dev
```

等价于：

```bash
./scripts/dev.sh
```

启动后访问：

```text
前端：http://localhost:5173
后端：http://localhost:8000
```

默认监听 `0.0.0.0`，可以通过局域网或服务器公网 IP 访问：

```text
前端：http://<server-ip>:5173
后端：http://<server-ip>:8000
```

前端默认使用同源 `/api` 访问后端，并由 Vite 代理到 FastAPI。这样远程浏览器访问 `http://<server-ip>:5173` 时，不会错误请求浏览器本机的 `localhost:8000`。

## 常用命令

```bash
make setup      # 安装 Python/前端依赖，并初始化 SQLite
make dev        # 一键启动后端 + 前端
make backend    # 只启动 FastAPI
make frontend   # 只启动 React/Vite
make init       # 初始化 SQLite
make daily      # 执行每日任务，生成日报
make check      # Python 编译检查 + 前端构建
make doctor     # 检查本地环境配置
make doctor-server # 检查服务器域名配置
make clean      # 清理依赖缓存和运行文件
```

## 数据源与每日流水线

每日任务默认优先尝试 AKShare；如果当前环境未安装 AKShare、网络不可用或接口失败，会自动降级为本地样本行情，保证开发和页面演示不中断。

启用真实数据源依赖：

```bash
uv sync --extra data
```

执行完整流水线：

```bash
make daily
```

输出包括：

```text
data/raw/market/*_manifest.json
data/parquet/daily_bar/
data/parquet/market_breadth/
data/parquet/sector_factor/
data/parquet/stock_factor/
reports/daily/YYYY-MM-DD.md
```

## 目录结构

```text
personal-invest/
├── docs/              # 设计目标、架构、需求边界
├── backend/           # FastAPI 后端
├── frontend/          # React 前端
├── worker/            # 数据同步、因子、策略、报告任务
├── scripts/           # 初始化、启动、检查脚本
├── storage/           # SQLite / DuckDB 文件
├── data/              # raw / parquet / tmp
└── reports/           # daily / weekly 报告
```

## 运行策略

- Python 依赖由根目录 `pyproject.toml` 管理。
- 后端通过 `uv run` 启动，不再使用 `pip install -r requirements.txt`。
- 前端通过 `pnpm -C frontend` 管理，不再使用 `npm install`。
- 默认通过 Corepack 使用 `pnpm@latest`，避免长期停留在旧版本。
- 日常开发优先使用 `make dev`。

## 远程访问配置

默认配置已经支持 `0.0.0.0`：

```text
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
FRONTEND_HOST=0.0.0.0
FRONTEND_PORT=5173
VITE_API_BASE=
```

如果前端和后端部署在不同域名或端口，并且不使用 Vite 代理，可以显式设置：

```bash
VITE_API_BASE=http://<server-ip>:8000 make dev
```

服务器需要放行端口：

```text
5173：前端页面
8000：后端 API
```

## 本地 / 服务器启动

本地开发：

```bash
cp .env.example .env
make dev
```

服务器开发，使用已配置的域名：

```bash
cp .env.server.example .env.server
make doctor-server
make dev:server
```

当前服务器域名配置：

```text
前端：https://invest.chalme.indevs.in
后端：https://api.chalme.indevs.in
```

关键环境变量：

```env
VITE_API_BASE=https://api.chalme.indevs.in
FRONTEND_ALLOWED_HOSTS=invest.chalme.indevs.in,localhost,127.0.0.1
BACKEND_CORS_ORIGINS=https://invest.chalme.indevs.in,http://localhost:5173,http://127.0.0.1:5173
```
