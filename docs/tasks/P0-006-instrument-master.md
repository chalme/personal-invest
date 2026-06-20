# P0-006: 引入资产主数据 instrument

- Status: TODO
- Priority: P0
- Owner: Codex
- Created At: 2026-06-21
- Completed At:

## Goal

新增资产主数据表，统一股票、ETF、场外基金的名称、类型、市场、行业/主题基础信息、风险等级、状态和来源。

## Scope

- 新增 `backend/migrations/003_instrument.sql`。
- 新增 `instrument` 表。
- 表字段包含 `symbol`、`name`、`asset_type`、`market`、`exchange`、`sector_code`、`sector_name`、`fund_type`、`risk_level`、`status`、`source`、`created_at`、`updated_at`。
- 从 `watchlist`、`portfolio_position`、`strategy_signal`、`investment_advice` 回填资产。
- 资产类型归一优先使用 `backend/app/core/asset_type.py`。

## Compatibility

- 短期保留 `watchlist.name`、`watchlist.asset_type`、`portfolio_position.name`、`portfolio_position.asset_type`。
- `instrument` 先作为主数据优先来源，不立即删除旧字段。
- 读取路径逐步接入，避免一次性大迁移。

## Acceptance

- `instrument` 能覆盖观察池、持仓、信号和建议中出现的资产。
- 重复执行回填不会产生重复资产。
- 观察池和持仓读取能优先使用 `instrument` 中的名称和资产类型。
- 旧字段仍可作为 fallback。

## Completion Markers

- Completed At:
- Changed Files:
- Verification:
- Notes:

