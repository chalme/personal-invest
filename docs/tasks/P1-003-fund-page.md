# P1-003: 新增基金分析 API 和页面

- Status: DONE
- Priority: P1
- Owner: Codex
- Created At: 2026-06-20
- Completed At: 2026-06-20

## Goal

新增独立基金分析页，与个股分析页并列，展示基金评分、净值趋势、收益、回撤、波动、结论和风险说明。

## Scope

- 新增基金分析 API。
- 新增基金净值趋势 API。
- 新增前端基金分析页面。
- 侧边栏和路由接入基金分析入口。

基金策略信号、日报和 AI 解释属于后续 P1-006。

## Changes

- 新增 `backend/app/api/funds.py`。
- 新增 `backend/app/services/fund_service.py`。
- 更新 `backend/app/main.py`。
- 新增 `frontend/src/pages/FundsPage.tsx`。
- 更新 `frontend/src/App.tsx`。
- 更新 `frontend/src/components/layout/AppLayout.tsx`。
- 更新 `frontend/src/api/types.ts`。

## Acceptance

- `GET /api/funds/analysis` 返回基金分析快照。
- `GET /api/funds/{symbol}/nav` 返回基金净值曲线。
- 前端侧边栏可进入基金分析页。
- 没有基金数据时页面显示空状态。

## Verification

- `scripts/init_db.py` 通过。
- `make daily` 通过。
- `make check` 通过。
