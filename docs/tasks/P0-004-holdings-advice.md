# P0-004: 个人持仓与分级建议底座

- Status: DONE
- Priority: P0
- Owner: Codex
- Created At: 2026-06-20
- Completed At: 2026-06-20

## Goal

支持默认个人组合，并为股票、ETF、场外基金生成可追溯的分级建议。

## Scope

- 新增 `investment_advice` 快照表。
- 每日任务生成规则建议。
- 建议区分真实持仓 `HOLDING` 和观察资产 `WATCHING`。
- 持仓页展示持仓建议和观察池建议。
- AI 组合解释只解释规则生成的建议，不直接生成不可追溯买卖结论。

## Advice Levels

- 继续观察
- 买入关注
- 持有
- 减仓关注
- 卖出关注

## Advice Fields

每条建议包含：

- 一句话结论
- 触发原因
- 关键指标
- 风险说明
- 复核动作
- 置信度
- 数据日期

## Changed Files

- `backend/migrations/001_init.sql`
- `scripts/init_db.py`
- `worker/strategy/signal_engine.py`
- `worker/daily_job.py`
- `backend/app/services/portfolio_service.py`
- `backend/app/services/ai_service.py`
- `frontend/src/api/types.ts`
- `frontend/src/pages/PortfolioPage.tsx`

## Verification

- `uv run python scripts/init_db.py`
- `uv run python worker/daily_job.py`
- `./scripts/check.sh`
- SQLite 验证 `investment_advice` 已生成持仓和观察池建议。

## Notes

本任务只提供规则生成、可追溯建议底座，不做自动交易，不替用户直接下单。
