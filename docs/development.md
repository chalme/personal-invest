# 开发与启动规范

## 结论

项目统一使用：

```text
uv 管理 Python 依赖
Corepack + pnpm latest 管理前端依赖
make dev / scripts/dev.sh 一键启动
```

## 为什么这样设计

个人项目需要低维护和快速启动，不能让开发流程变成负担。

- `uv`：比传统 `venv + pip` 更简单，依赖、虚拟环境和命令执行统一管理。
- `pnpm latest`：前端依赖安装快、磁盘占用更低，并统一跟随最新稳定版本。
- `Makefile`：作为统一入口，减少记忆成本。
- `scripts/*.sh`：保证没有 make 的环境也能直接启动。

## 快速启动

```bash
make dev
```

或：

```bash
./scripts/dev.sh
```

脚本会自动执行：

```text
uv sync
corepack prepare pnpm@latest --activate
pnpm install
初始化 SQLite
启动 FastAPI
启动 Vite
```

## pnpm 版本策略

默认使用最新稳定版：

```bash
corepack prepare pnpm@latest --activate
```

日常无需手动执行，`scripts/setup.sh`、`scripts/dev.sh`、`scripts/frontend.sh`、`scripts/check.sh` 会自动处理。

需要临时固定版本时：

```bash
PNPM_VERSION=11 make dev
PNPM_VERSION=latest make dev
```

项目不在 `frontend/package.json` 中锁死 `packageManager`，避免 Corepack 被旧版本字段强制回退。

## 单独启动

后端：

```bash
make backend
```

前端：

```bash
make frontend
```

每日任务：

```bash
make daily
```

## 环境变量

默认配置：

```text
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
FRONTEND_HOST=0.0.0.0
FRONTEND_PORT=5173
VITE_API_BASE=
```

可以复制 `.env.example` 后自行调整。

## 0.0.0.0 访问

开发环境默认同时支持本机和远程访问：

```text
本机前端：http://localhost:5173
本机后端：http://localhost:8000
远程前端：http://<server-ip>:5173
远程后端：http://<server-ip>:8000
```

前端默认 `VITE_API_BASE` 为空，浏览器会请求同源 `/api`，再由 Vite 代理到后端 `127.0.0.1:8000`。这个设计避免远程访问时浏览器错误请求自己的 `localhost:8000`。

需要直连后端时再显式设置：

```bash
VITE_API_BASE=http://<server-ip>:8000 make dev
```

如果使用云服务器，需要在安全组/防火墙放行：

```text
5173 前端页面
8000 后端 API
```

## 生产模式

开发模式使用 Vite dev server，适合热更新；服务器长期运行建议使用生产模式。

```bash
make prod-server
```

生产模式会：

```text
pnpm -C frontend build
部署阶段执行 `uv sync`
FastAPI 使用 `.venv/bin/python` 非 reload 模式启动
静态服务托管 frontend/dist
```

单独启动：

```bash
make backend-prod
make frontend-prod
```

生产模式日志：

```text
logs/backend-prod.log
logs/frontend-prod.log
```

边界：`make prod-server` 仍是前台组合进程；长期运行请使用 systemd 模板。生产运行时不要求 `uv` 出现在 systemd PATH，但要求 `.venv/bin/python` 已存在。

## 日志

`make dev` 会把日志写入：

```text
logs/backend.log
logs/frontend.log
```

## 边界

- 不使用 Spring Boot。
- 不使用 Go。
- 不使用 PostgreSQL。
- 不使用 npm 作为默认包管理器。
- 不在项目里锁死旧 pnpm 版本，默认跟随 `pnpm@latest`。
- 不使用 pip/venv 作为默认 Python 依赖管理方式。

## 本地与服务器域名配置

项目支持通过环境文件切换本地和服务器启动配置。

### 本地开发

```bash
cp .env.example .env
make dev
```

默认访问：

```text
前端：http://localhost:5173
后端：http://localhost:8000
```

本地默认 `VITE_API_BASE` 留空，前端请求 `/api`，由 Vite 代理到本机后端。

### 服务器开发

```bash
cp .env.server.example .env.server
make dev:server
```

当前服务器域名建议配置：

```env
VITE_API_BASE=https://api.chalme.indevs.in
FRONTEND_ALLOWED_HOSTS=invest.chalme.indevs.in,localhost,127.0.0.1
BACKEND_CORS_ORIGINS=https://invest.chalme.indevs.in,http://localhost:5173,http://127.0.0.1:5173
```

访问：

```text
前端：https://invest.chalme.indevs.in
后端：https://api.chalme.indevs.in
```

`FRONTEND_ALLOWED_HOSTS` 解决 Vite dev server 的 Host 白名单问题；`BACKEND_CORS_ORIGINS` 解决浏览器跨域访问后端 API 的问题。

## 生产部署边界

生产环境建议把 Personal Invest 分成三个边界看待：

```text
浏览器
  ↓
Cloudflare Access / HTTPS / 域名
  ↓
invest.chalme.indevs.in 前端静态服务
  ↓
api.chalme.indevs.in 后端 API
  ↓
SQLite / Parquet / reports 本地数据
```

第一阶段不做应用内多用户登录，推荐把访问保护放在 Cloudflare Access：

- `invest.chalme.indevs.in` 必须受 Access 保护。
- `api.chalme.indevs.in` 也必须受 Access 保护，不能只保护前端。
- 后端源站端口不应直接公网裸露，避免绕过 Access 访问 API。
- 服务器 IP 直连、`8000` 后端端口和静态前端端口应由防火墙、反向代理或 Tunnel 限制。

健康检查边界：

- `/health` 只返回最小状态，不暴露路径、密钥或数据库位置。
- `/health/cors` 只用于 CORS 诊断，允许展示前端公网域名和 CORS regex，不应暴露敏感配置。
- `scripts/health.sh` 只能作为自动 smoke check，不能替代真实浏览器人工验收。

人工配置清单：

1. 在 Cloudflare Access 中为前端和 API 各创建或绑定应用。
2. 限制授权用户、邮箱或身份提供方。
3. 确认服务器源站端口不能被公网直接访问。
4. 确认 `.env.server` 和密钥文件不进入 Git。
5. 在真实浏览器中完成 `MANUAL-001` 回归验收。

Code Agent 可提供文档、systemd 模板、备份脚本和健康检查脚本；Cloudflare、服务器防火墙和 Secret 配置必须由人工完成。

## systemd 长期运行模板

项目提供第一版 systemd 模板：

```text
deploy/systemd/personal-invest-backend.service
deploy/systemd/personal-invest-frontend.service
```

使用方式需要人工在服务器执行：

```bash
sudo cp deploy/systemd/personal-invest-backend.service /etc/systemd/system/
sudo cp deploy/systemd/personal-invest-frontend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now personal-invest-backend.service
sudo systemctl enable --now personal-invest-frontend.service
```

部署或更新模板后，如果曾经启动失败，先执行：

```bash
sudo systemctl reset-failed personal-invest-backend.service
sudo systemctl reset-failed personal-invest-frontend.service
```

常用命令：

```bash
sudo systemctl status personal-invest-backend.service
sudo systemctl status personal-invest-frontend.service
sudo journalctl -u personal-invest-backend.service -f
sudo journalctl -u personal-invest-frontend.service -f
sudo systemctl restart personal-invest-backend.service
sudo systemctl restart personal-invest-frontend.service
```

模板默认：

- 工作目录：`/root/remote/personal-invest`
- 环境文件：`.env.server`
- 后端启动：`/root/remote/personal-invest/scripts/backend_prod.sh`
- 前端启动：`/root/remote/personal-invest/scripts/frontend_prod.sh`
- 前端 systemd 模板：`FRONTEND_BUILD_ON_START=0`，只服务已构建的 `frontend/dist`，避免运行时依赖 `pnpm`
- Python 运行时：`/root/remote/personal-invest/.venv/bin/python`
- 异常退出自动重启：`Restart=on-failure`

注意：模板只提供长期运行基础，不负责 Cloudflare Access、防火墙、Secret 管理或人工浏览器验收。
