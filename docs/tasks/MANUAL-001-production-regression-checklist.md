# MANUAL-001: 线上功能人工回归验收

- Status: TODO
- Priority: P1
- Owner: Human
- Created At: 2026-06-21
- Completed At:

## Goal

在真实浏览器和线上域名下确认系统可用性。该任务需要人工观察页面展示、浏览器 Network、交互体验和线上缓存行为，不能完全由自动化脚本替代。

## Scope

这是人工 checklist，不进入开发主线。验收发现 bug 时，再单独拆 bugfix 任务。

## Checklist

### Deploy

- [ ] `git pull`
- [ ] `uv run python scripts/migrate_db.py`
- [ ] `uv run python worker/daily_job.py`
- [ ] `make prod-server`

### Runtime Config / CORS

- [ ] `/config.js` 中 `apiBase` 指向后端 API 域名。
- [ ] `/health/cors` 显示前端域名或 CORS regex。
- [ ] 浏览器 Network 无 CORS / fetch error。
- [ ] Dashboard API 请求目标正确。

### Pages

- [ ] Dashboard 正常加载。
- [ ] 股票页显示财报与估值快照。
- [ ] 基金 / ETF 页显示基金深度与 ETF 深度分析。
- [ ] 复盘页显示重要事项、决策记录和后续结果。
- [ ] 设置页主题和密度设置可保存并生效。

### Data / Review Loop

- [ ] 财报异常能进入重要事项。
- [ ] ETF 深度异常能进入重要事项。
- [ ] 决策记录可以独立创建。
- [ ] outcome 文案不表达简单“正确 / 错误”。

## Notes

该任务依赖真实浏览器和线上环境。自动 smoke test 只能辅助，不能替代人工确认。
