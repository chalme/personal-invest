# P1-014: Decision Outcome Tracking

- Status: DONE
- Priority: P1
- Owner: Codex
- Created At: 2026-06-21
- Completed At: 2026-06-21

## Goal

自动跟踪决策后 1D / 1W / 1M 的轻量结果，帮助复盘“后来发生了什么”。

## Scope

第一版只做结果摘要，不做复杂收益归因、超额收益、交易成本归因或多账户评价。

## Concrete Changes

- 新增 `decision_outcome` 表，按 `decision_id + horizon` 唯一。
- `horizon` 支持 `1D`、`1W`、`1M`。
- 记录决策时和跟踪时的价格/净值、收益、建议等级、风险数量和摘要。
- 新增 `worker/review/outcome_tracker.py`，daily job 自动刷新到期 outcome。
- Review API 提供决策 outcome 查询。

## Acceptance

- 每个决策最多生成三条 outcome。
- 重复执行 outcome tracker 幂等。
- 缺少价格或净值时不报错，并保留可解释的缺失状态。
- 文案明确 outcome 只是复盘参考，不代表决策绝对正确或错误。

## Verification

- 迁移重复执行幂等。
- 构造已有决策后，1D / 1W / 1M outcome 可生成或保持缺失说明。
- Python 编译和前端构建通过。

## Notes

- 卖出后上涨不一定代表决策错误，页面需要避免做简单裁判。


## Completed Changes

- Added `decision_outcome` table with unique `(decision_id, horizon)`.
- Added `worker/review/outcome_tracker.py` for 1D / 1W / 1M outcome refresh.
- Daily job now refreshes decision outcomes before building the report.
- Added Review API outcome listing endpoints.

## Completed Verification

- Migration applied through `scripts/migrate_db.py`.
- Outcome tracker repeated execution stayed idempotent through upsert.
- A historical smoke decision produced outcome rows.
- Python compile, frontend build and `./scripts/check.sh` passed.
