# P1-007: 市场与行业全景分析

## Goal

市场分析不只展示市场分数和少数强势行业，而是覆盖热门、冷门、轮动、防守、过热行业，并映射到股票、ETF、基金观察对象。

## Scope

- 新增行业全景服务和 API。
- 行业分组覆盖：过热、热门、轮动、防守、冷门、中性观察。
- 行业结果映射到观察池资产，包含股票、ETF、场外基金。
- Dashboard 展示行业全景摘要。
- 行业页展示分组、解释和观察资产映射。

## API

- `GET /api/market/sectors/panorama`

## Changed Files

- `backend/app/services/market_service.py`
- `backend/app/api/market.py`
- `backend/app/services/dashboard_service.py`
- `frontend/src/api/types.ts`
- `frontend/src/pages/Dashboard.tsx`
- `frontend/src/pages/SectorsPage.tsx`

## Verification

- `uv run python worker/daily_job.py`
- `uv run python` 调用 `MarketService().sector_panorama()` 验证输出结构。
- `./scripts/check.sh`

## Notes

当前版本不新增行业全景表，直接基于最新 `sector_trend_snapshot` 和观察池映射实时生成，避免过早扩大数据模型。
