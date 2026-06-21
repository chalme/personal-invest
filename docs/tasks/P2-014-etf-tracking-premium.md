# P2-014: ETF 跟踪质量与折溢价

- Status: DONE
- Priority: P2
- Owner: Codex
- Created At: 2026-06-21
- Completed At: 2026-06-21

## Goal

建立 ETF / LOF 跟踪误差、跟踪偏离、折溢价和指数拟合质量快照。

## Scope

本任务只做数据模型、worker 和 service 读取。页面、AI、日报和复盘闭链接入放到 `P2-015`。

跟踪质量对指数和净值数据依赖较强，第一版必须优先保证数据可信度。

## Concrete Changes

- 新增 ETF 跟踪质量快照表，如 `etf_tracking_snapshot`。
- 在可得指数、价格、净值数据时计算跟踪误差、跟踪偏离、折溢价和拟合质量。
- 数据不足时输出 `MISSING` 或 `ESTIMATED`，并保留原因说明。
- daily job 接入 ETF 跟踪质量计算步骤。

## Acceptance

- ETF 跟踪质量不会用假数据冒充真实指标。
- 能区分真实、估算和缺失三种数据状态。
- 跟踪异常可供后续 `risk_event` 和 `review_task` 接入。
- 无指数或净值数据时 worker 不失败。

## Verification

- `uv run python scripts/migrate_db.py`
- `uv run python -m worker.etf.tracking_quality`
- 查询 ETF 跟踪质量表。
- `uv run python -m compileall backend/app worker scripts`
- `./scripts/check.sh` 当前环境缺少 `pnpm`，未能完成前端阶段。

## Changed Files

- `backend/migrations/018_etf_tracking_quality.sql`
- `worker/etf/tracking_quality.py`
- `backend/app/services/etf_deep_service.py`
- `worker/daily_job.py`

## Notes

- 如果第一版指数数据不足，可以先落 `MISSING` / `ESTIMATED`，不强行生成确定性跟踪误差。
