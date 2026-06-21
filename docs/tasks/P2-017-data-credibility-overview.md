# P2-017: 数据可信度总览 V1

- Status: DONE
- Priority: P2
- Owner: Codex
- Created At: 2026-06-21
- Completed At: 2026-06-21

## Goal

提供统一的数据可信度总览，让用户知道当前市场、行情、股票财报、基金深度、ETF 深度、复盘等模块分别使用真实、估算、样本还是缺失数据。

## Scope

第一版只做可见性和解释，不重写所有建议规则。

需要覆盖：

- 市场 / 行情数据。
- 股票财报与估值快照。
- 场外基金画像、风险收益、基准/同类和暴露。
- ETF 画像、暴露、流动性、风险收益、跟踪质量。
- 组合快照与复盘事项。

不做：

- 真实数据源全面接入。
- 外部供应商配置 UI。
- 建议规则大改。
- 线上人工回归验收。

## Concrete Changes

### Backend

- 新增 `backend/app/services/data_credibility_service.py`。
- 新增 API：`GET /api/data/credibility`。
- 聚合各模块的：
  - `source_mode`
  - `latest_data_date`
  - `record_count`
  - `coverage_ratio`
  - `can_drive_advice`
  - `risk_level`
  - `note`

建议模块枚举：

- `market_data`
- `daily_bar`
- `fund_nav`
- `stock_financial`
- `fund_deep`
- `etf_deep`
- `portfolio_snapshot`
- `review_loop`

### Frontend

- `Dashboard` 增加数据可信度摘要，只展示整体状态和关键风险。
- `SettingsPage` 增加完整数据可信度表格。
- `frontend/src/api/types.ts` 增加可信度类型。

### Data Semantics

- `REAL`：可参与规则建议和高置信解释。
- `ESTIMATED`：可展示和低置信解释，不应单独触发高优先级建议。
- `SAMPLE`：只能用于演示和展示，不应驱动高置信建议。
- `MISSING`：只展示缺失，不生成确定性结论。
- `MIXED`：不同模块混合存在以上状态。

## Acceptance

- `GET /api/data/credibility` 返回全局摘要和模块列表。
- Dashboard 能看到整体可信度、真实/估算/样本/缺失计数和最新数据日期。
- Settings 能看到各模块 `source_mode`、日期、覆盖数量、是否参与建议和说明。
- 股票财报、场外基金深度、ETF 深度都被统计。
- 没有 `FUND` 时显示基金深度为 `MISSING`，不能把 ETF 混成 FUND。
- `SAMPLE`、`ESTIMATED`、`MISSING` 有明确中文说明。
- 前端构建通过。

## Verification

- `uv run python scripts/migrate_db.py`
- `PYTHONPATH=backend uv run python` smoke test `DataCredibilityService`
- `cd frontend && pnpm build`
- `./scripts/check.sh`

## Completion

- Added `DataCredibilityService` and `GET /api/data/credibility`.
- Dashboard now shows a compact credibility summary.
- Settings now shows the full module-level credibility table.
- The service distinguishes `REAL`, `ESTIMATED`, `SAMPLE`, `MISSING`, and `MIXED`.

## Notes

这是数据可信度可见性任务。真实财报、真实基金画像和真实 ETF 跟踪数据源接入应另拆后续任务。
