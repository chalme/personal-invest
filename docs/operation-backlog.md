# 服务器长期运行待办

本文档记录当前项目从“开发可用”升级到“服务器长期稳定运行”需要补齐的运维能力。

这些事项不是页面展示需求，也不是当前 MVP 阻塞项；它们作为后续运维增强任务保留。

## 当前状态

- MVP 已完成并已推送到 GitHub。
- 当前可通过 `make prod-server` 在服务器生产模式启动。
- 当前生产启动仍是前台进程，适合验证，不适合作为长期无人值守方案。

## 任务索引

人工参与任务：

- `H-002`：Cloudflare Access 配置。
- `H-003`：源站端口与服务器防火墙确认。
- `H-004`：生产 Secret 与敏感配置确认。
- `H-005`：备份目标与恢复策略确认。

Code Agent 可独立推进任务：

- `OPS-DOC-001`：生产部署边界文档。
- `OPS-002`：本地备份脚本任务。
- `OPS-003`：systemd 服务模板。
- `OPS-004`：生产健康检查脚本。

边界：人工任务需要生产账号、服务器或安全配置权限；Code Agent 任务只提供文档、脚本、模板和检查逻辑，不直接执行生产配置。


## 生产部署边界

推荐第一阶段生产边界：

```text
浏览器 -> Cloudflare Access -> 前端域名 invest.chalme.indevs.in
浏览器 -> Cloudflare Access -> API 域名 api.chalme.indevs.in
API -> 本机 SQLite / Parquet / reports
```

人工必须确认：

- 前端和 API 都被 Access 保护。
- 后端端口不能通过服务器 IP 或公网端口绕过 Access。
- `/health` 不输出敏感配置。
- `/health/cors` 仅用于 CORS 诊断。
- `.env.server`、API key、备份文件和生产日志不进入 Git。

Code Agent 可交付：

- systemd 模板。
- 本地备份脚本。
- 生产健康检查脚本。
- 部署边界文档和人工 checklist。

Code Agent 不执行：

- Cloudflare 账号配置。
- 服务器安全组或防火墙变更。
- Secret 内容审计。
- 真实浏览器人工验收。

## 待办事项

### 1. systemd 守护启动

目标：让前端和后端可以长期运行、自动重启、开机自启。

计划内容：

- `personal-invest-backend.service`
- `personal-invest-frontend.service`
- 开机自启
- 异常自动重启
- 日志统一输出

优先级：高。

### 2. 访问保护

目标：公网访问前先鉴权，避免个人投资数据、持仓、建议和复盘记录被无权限访问。

当前已经通过 Cloudflare 代理域名，但 Cloudflare 普通代理 / CDN / WAF 不等同于登录鉴权。第一阶段推荐使用 Cloudflare Access 作为外层访问保护。

可选方案：

- Cloudflare Access
- Basic Auth
- 应用内登录
- API Token

推荐方案：优先使用 Cloudflare Access，减少代码改动。

保护范围：

- 前端域名：`invest.chalme.indevs.in`
- API 域名：`api.chalme.indevs.in`

验收标准：

- 未登录访问前端域名时，应进入 Cloudflare Access 登录页。
- 未登录访问 API 域名时，应被 Cloudflare Access 拦截。
- 已授权账号登录后，前端页面和 API 请求正常。
- 直接访问服务器 IP 和后端端口不能绕过访问保护。
- `/health` 只保留最小健康信息，不暴露敏感配置。

后续任务：

- `P0-008`：Cloudflare Access 访问保护与部署边界。
- `SEC-P1-001`：应用内单用户登录。
- `SEC-P1-002`：API Token，用于脚本、自动化或移动端调用。

参考：

- [Cloudflare Access applications](https://developers.cloudflare.com/cloudflare-one/access-controls/applications/)
- [Cloudflare HTTP/self-hosted applications](https://developers.cloudflare.com/cloudflare-one/access-controls/applications/http-apps/)

优先级：高。

### 3. 数据备份

目标：避免 SQLite、Parquet、报告和配置丢失。

需要备份：

- `storage/invest.db`
- `data/parquet/`
- `reports/`
- `config.yaml`
- `.env.server`

计划内容：

- `scripts/backup.sh`
- `make backup`
- 定期备份到 `backups/`

优先级：高。

### 4. 生产健康检查

目标：快速确认前后端、域名和 API 是否正常。

计划内容：

- `scripts/health.sh`
- `make health`
- 检查前端端口 `5173`
- 检查后端端口 `8000`
- 检查 `/health`
- 检查线上域名访问

优先级：中。

### 5. 真实数据源增强

目标：减少样本数据 fallback，增强真实市场数据质量。

计划内容：

- AKShare 稳定接入
- 交易日历
- 指数真实数据
- 行业真实数据
- 财务指标数据
- 估值数据
- 数据失败重试
- 数据版本记录

优先级：中。

## 边界说明

以上任务用于提升服务器长期运行能力，不影响当前 MVP 的核心使用路径。

当前 MVP 核心路径仍然是：

```text
make daily
make prod-server
```

浏览器访问：

```text
https://invest.chalme.indevs.in
```


### 本地备份脚本

第一版已提供：

```bash
make backup
# or
BACKUP_ROOT=/path/to/backups ./scripts/backup.sh
```

默认备份内容：

- `storage/invest.db`
- `data/parquet/`
- `reports/`
- `config.yaml`
- `.env.server.example`

`.env.server` 默认不备份，因为可能包含密钥。真实备份目标、加密、异地保存和保留周期仍由人工在 `H-005` 中确认。

## systemd 模板使用说明

`OPS-003` 已提供：

- `deploy/systemd/personal-invest-backend.service`
- `deploy/systemd/personal-invest-frontend.service`

人工启用前必须确认：

- 仓库实际路径是否为 `/root/remote/personal-invest`。
- `.env.server` 已存在且未进入 Git。
- 前端和 API 域名已经由 Cloudflare / 反向代理指向正确端口。
- 源站端口不会绕过访问保护裸露。

模板可以复制到 `/etc/systemd/system/` 后启用，但 Code Agent 不直接在生产机执行 `systemctl enable --now`。


## 生产健康检查脚本

`OPS-004` 已提供：

```bash
make health-server
```

该命令会检查：

- 前端页面 HTTP 状态。
- `/config.js` 是否可访问。
- 后端 `/health`。
- 后端 `/health/cors`。
- `/api/dashboard`。
- `/api/data/credibility`。
- 使用 `FRONTEND_PUBLIC_URL` 作为 Origin 时是否返回 CORS header。

可通过环境变量覆盖：

```bash
FRONTEND_PUBLIC_URL=https://invest.chalme.indevs.in API_BASE=https://api.chalme.indevs.in ./scripts/health.sh
```

该脚本只做自动 smoke check，不能替代 `MANUAL-001` 的真实浏览器人工回归验收。
