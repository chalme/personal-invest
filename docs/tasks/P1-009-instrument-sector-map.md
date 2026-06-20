# P1-009: 新增资产行业/主题映射

- Status: DONE
- Priority: P1
- Owner: Codex
- Created At: 2026-06-21
- Completed At: 2026-06-21

## Goal

建立资产到行业、主题、指数、地区和风格的正式暴露映射，替代单纯依赖 `watchlist.group_name` 的弱映射。

## Scope

- 新增 `backend/migrations/006_instrument_sector_map.sql`。
- 新增 `instrument_sector_map` 表。
- 字段包含 `symbol`、`map_type`、`sector_code`、`sector_name`、`weight`、`source`、`updated_at`。
- 主键为 `(symbol, map_type, sector_code)`。
- `map_type` 支持 `SECTOR`、`THEME`、`INDEX`、`REGION`、`STYLE`。
- 行业全景优先读取映射表，没有映射时 fallback 到 `watchlist.group_name`。

## Business Meaning

这张表不只是行业映射，也是资产暴露映射。ETF 和基金可能对应宽基指数、红利风格、海外地区、债券、商品或多个主题。

## Acceptance

- 一个资产可以映射多个行业、主题、指数、地区或风格。
- 行业全景能通过正式映射关联股票、ETF 和基金。
- 旧的 `watchlist.group_name` 仍可作为兜底来源。
- 页面解释不把主题、指数和地区误写成传统行业。

## Completion Markers

- Completed At: 2026-06-21
- Changed Files:
- Verification:
- Notes:

