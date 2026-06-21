# P2-010: 场外基金基准 / 同类比较与暴露

- Status: TODO
- Priority: P2
- Owner: Codex
- Created At: 2026-06-21
- Completed At:

## Goal

落地场外基金的基准比较、同类比较和持仓暴露分析。

## Scope

本任务只做 `FUND` 的比较和暴露层，不做 ETF 指数暴露与跟踪质量。

## Concrete Changes

- 新增 `fund_benchmark_snapshot`。
- 新增 `fund_peer_rank_snapshot`。
- 新增 `fund_holding_exposure_snapshot`。
- 计算相对基准收益、同类排名 / 分位、风格暴露和重复暴露风险。

## Acceptance

- 场外基金能解释是否跑赢基准、同类位置如何、是否与组合重复暴露。
- 比较结果能供页面、建议和复盘读取。

## Verification

- worker 执行后能查询到比较和暴露数据。
- `rtk git diff --check`。

## Notes

- ETF 指数暴露与跟踪质量继续留给后续 ETF 深度实现。
