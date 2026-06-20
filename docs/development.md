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
