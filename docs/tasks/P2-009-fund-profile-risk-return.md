# P2-009: 场外基金画像与风险收益快照

- Status: TODO
- Priority: P2
- Owner: Codex
- Created At: 2026-06-21
- Completed At:

## Goal

落地场外基金画像、经理 / 公司信息和风险收益快照。

## Scope

本任务只做场外基金基础画像和风险收益计算，不做 ETF / LOF。

## Concrete Changes

- 新增 `fund_profile`。
- 新增 `fund_manager_profile`。
- 新增 `fund_company_profile`。
- 新增 `fund_risk_return_snapshot`。
- 计算阶段收益、最大回撤、波动、夏普、卡玛和回撤修复时间。

## Acceptance

- `FUND` 资产能生成基础画像和风险收益快照。
- 页面、建议和复盘后续可读取这些快照。
- ETF / LOF 不混入本任务。

## Verification

- 迁移可重复执行。
- worker 执行后能查询到画像和风险收益数据。
- `rtk git diff --check`。

## Notes

- 不在本任务内落地基准 / 同类比较。
