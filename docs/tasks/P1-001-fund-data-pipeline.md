# P1-001: 新增基金数据管线

- Status: DONE
- Priority: P1
- Owner: Codex
- Created At: 2026-06-20
- Completed At: 2026-06-20

## Goal

支持场外基金净值数据集。ETF / LOF 仍按场内行情写入 daily_bar，场外基金写入 fund_nav。

## Scope

本任务只完成基金净值采集和落盘：

- 从观察池中筛选 asset_type 为 FUND 的标的。
- 优先尝试 AKShare 基金净值。
- 失败时生成样本净值，保证流水线不中断。
- 没有基金时每日任务返回 0 行并继续运行。

基金分析快照、基金 API 和基金页面属于后续任务。

## Changes

- 在 worker/ingest/market_data.py 中新增基金净值同步逻辑。
- 新增 fund_nav Parquet 数据集。
- 新增 raw fund manifest。
- daily job 接入基金净值同步步骤。

## Acceptance

- 每日任务能产出或跳过 fund_nav，不影响股票行情流水线。
- 基金数据记录 source_count、latest_nav_date 和 generated_at。
- 没有基金时任务正常完成。

## Verification

- daily job 通过。
- make check 通过。
