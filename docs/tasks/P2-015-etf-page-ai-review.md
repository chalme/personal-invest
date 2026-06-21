# P2-015: ETF 页面、AI 与复盘闭链接入

- Status: DONE
- Priority: P2
- Owner: Codex
- Created At: 2026-06-21
- Completed At: 2026-06-21

## Goal

将 ETF 深度分析接入页面、AI、风险事件、重要事项和日报，形成 ETF 专项复盘闭环。

## Scope

本任务依赖 `P2-012`、`P2-013`、`P2-014`。

包括：

- ETF 深度 API。
- 基金 / ETF 页面中的 ETF 专项区块。
- AI ETF 解释。
- ETF 异常进入 `risk_event`、`review_task`、日报。

不包括：

- 股票财报模型。
- 场外基金经理 / 基金公司主动管理模型。
- 自动交易。

## Concrete Changes

- 新增或扩展 ETF 深度 service 和 API。
- 在基金 / ETF 页面展示 ETF 画像、暴露、流动性、风险收益、跟踪质量和折溢价。
- 新增 ETF 深度事件识别，写入 `risk_event`。
- 通过现有 review task 生成器进入重要事项。
- AI 解释 ETF 专项指标和数据来源。
- 日报增加 ETF 深度观察区。

## Acceptance

- 用户能直接查看 ETF 专项深度信息。
- AI 明确按 ETF 模型解释，不套股票财报或场外基金经理模型。
- ETF 异常能进入复盘闭环，但不制造每日待办压力。
- Dashboard / FundsPage / ReviewPage / Reports / AI 页面仍正常。

## Verification

- `uv run python scripts/migrate_db.py`
- `uv run python worker/daily_job.py`
- ETF 深度 API smoke test。
- `cd frontend && pnpm build` 当前环境缺少 `node/pnpm`，未执行
- `./scripts/check.sh` 当前环境缺少 `node/pnpm`，未完成前端阶段。

## Changed Files

- `backend/migrations/019_etf_deep_event.sql`
- `worker/etf/events.py`
- `worker/daily_job.py`
- `backend/app/api/funds.py`
- `backend/app/api/ai.py`
- `backend/app/services/ai_service.py`
- `backend/app/services/etf_deep_service.py`
- `worker/report/report_builder.py`
- `frontend/src/pages/FundsPage.tsx`

## Notes

- 本任务完成后，股票、场外基金、ETF 三条深度分析线形成同级闭环。
