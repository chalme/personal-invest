# P1-002: 新增基金分析快照

- Status: DONE
- Priority: P1
- Owner: Codex
- Created At: 2026-06-20
- Completed At: 2026-06-20

## Goal

基金不套用股票基本面/估值模型，改用净值收益、回撤、波动和趋势评分生成独立分析快照。

## Scope

本任务只完成数据层和 worker 层：

- 新增 `fund_analysis_snapshot` 表。
- 读取 `fund_nav` Parquet 数据集。
- 计算近 1/3/6 月收益、最大回撤、年化波动、趋势评分、风险评分和综合评分。
- 生成基金状态、结论和风险说明。
- daily job 接入基金分析步骤。

基金 API、基金页面、基金信号和日报 AI 输出属于后续任务。

## Changes

- 新增 `worker/factor/fund_analysis.py`。
- 更新 `backend/migrations/001_init.sql`。
- 更新 `worker/daily_job.py`。

## Acceptance

- 没有基金净值数据时任务跳过，不影响每日流水线。
- 有基金净值数据时能写入 `fund_analysis_snapshot`。
- 分析结果可解释评分来源。

## Verification

- `scripts/init_db.py` 通过。
- `make daily` 通过。
- `make check` 通过。
