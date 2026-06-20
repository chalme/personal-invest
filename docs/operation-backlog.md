# 服务器长期运行待办

本文档记录当前项目从“开发可用”升级到“服务器长期稳定运行”需要补齐的运维能力。

这些事项不是页面展示需求，也不是当前 MVP 阻塞项；它们作为后续运维增强任务保留。

## 当前状态

- MVP 已完成并已推送到 GitHub。
- 当前可通过 `make prod-server` 在服务器生产模式启动。
- 当前生产启动仍是前台进程，适合验证，不适合作为长期无人值守方案。

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

目标：避免公网域名被无权限访问。

可选方案：

- Cloudflare Access
- Basic Auth
- 应用内登录
- API Token

推荐方案：优先使用 Cloudflare Access，减少代码改动。

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

