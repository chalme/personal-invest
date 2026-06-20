# P0-007: 修正 ETF 独立分析口径

- Status: DONE
- Priority: P0
- Owner: Codex
- Created At: 2026-06-21
- Completed At: 2026-06-21

## Goal

ETF 使用价格型分析口径，不再复用股票基本面、公司质量和估值分析逻辑。

## Scope

- 新增 `backend/migrations/004_fund_analysis_type.sql`。
- `fund_analysis_snapshot` 增加 `analysis_type TEXT NOT NULL DEFAULT 'FUND_NAV'`。
- `FUND` 使用 `FUND_NAV`，基于场外基金净值。
- `ETF` 使用 `ETF_PRICE`，基于 `daily_bar` 价格序列。
- 信号和建议优先读取 `fund_analysis_snapshot where analysis_type = 'ETF_PRICE'`。
- 基金页继续作为 ETF/基金分析入口，但文案区分“ETF 价格分析”和“基金净值分析”。

## Out Of Scope

- 不新增独立 `etf_analysis_snapshot`。
- 不做复杂 ETF 成分股穿透。
- 不引入实时行情或券商接口。

## Acceptance

- ETF 不再新写入 `stock_analysis_snapshot`。
- ETF 分析不依赖 `fundamental_score`、`valuation_score` 或公司质量口径。
- ETF 建议和信号来自 `ETF_PRICE` 分析结果。
- 页面能展示 ETF 的分析来源，避免把 ETF 解释成普通股票或场外基金。

## Completion Markers

- Completed At: 2026-06-21
- Changed Files:
- Verification:
- Notes:

