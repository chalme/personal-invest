# QUOTE-001: 只读实时报价服务

- Status: TODO
- Priority: P0
- Owner: Codex
- Created At: 2026-06-21

## Goal

新增只读实时报价服务，为持仓录入、资产识别和市值估算提供真实报价辅助。报价服务只能返回真实公开源、真实历史缓存或 `MISSING`，不能生成 sample/mock/demo/estimated。

## Why

当前添加持仓需要用户手工填写代码、名称、资产类型和现价，录入成本高且容易污染收益计算。系统已经具备 real-only 行情同步和 provider chain，但缺少一个轻量、只读、面向表单交互的报价接口。

核心矛盾：

- 添加持仓需要低摩擦自动补价。
- 免费实时源不稳定，不能作为交易级行情。
- 投资建议仍应由日线同步和数据可信度门控驱动。

## Scope

- 新增报价 API：`GET /api/quotes/{symbol}`。
- 可选新增搜索 API：`GET /api/quotes/search?q=...`。
- 新增 `QuoteService`，统一返回名称、资产类型、价格、来源、时间和 warning。
- A股和 ETF 优先使用真实实时公开源；失败后使用本地最新 `daily_bar` 真实缓存。
- 基金第一版优先使用本地最新 `fund_nav`；如接实时估值源，必须单独标注来源和时间。
- 返回 `source_mode`：`REAL_QUOTE` / `REAL_CACHED` / `MISSING`。
- 返回 `source_provider`、`source_interface`、`price_time`、`trade_date`、`warning`。

## Out of Scope

- 不写入 `daily_bar` 或 `fund_nav`。
- 不把实时价格沉淀为历史日线。
- 不做自动交易、高频行情、盘口、Level-2 或成交撮合。
- 不把实时价格直接用于高置信投资建议。
- 不接券商账户。
- 不恢复 sample/mock/demo/estimated。

## Architecture

```mermaid
flowchart TD
    UI[Portfolio Entry Form] --> API[GET /api/quotes/{symbol}]
    API --> QS[QuoteService]
    QS --> RT[Realtime Public Source]
    QS --> CACHE[Local Real Cache]
    QS --> MISS[MISSING]

    RT -->|success| REAL[REAL_QUOTE]
    RT -->|failure| CACHE
    CACHE -->|latest daily_bar/fund_nav| RC[REAL_CACHED]
    CACHE -->|not found| MISS

    REAL --> UI
    RC --> UI
    MISS --> UI
```

## Data Contract

Suggested response:

```json
{
  "symbol": "600519.SH",
  "name": "贵州茅台",
  "asset_type": "STOCK",
  "price": 1720.0,
  "price_time": "2026-06-21T10:30:00+08:00",
  "trade_date": "2026-06-21",
  "source_mode": "REAL_QUOTE",
  "source_provider": "eastmoney",
  "source_interface": "stock_zh_a_spot_em",
  "warning": null
}
```

Fallback response:

```json
{
  "symbol": "600519.SH",
  "name": "贵州茅台",
  "asset_type": "STOCK",
  "price": 1688.0,
  "price_time": null,
  "trade_date": "2026-06-18",
  "source_mode": "REAL_CACHED",
  "source_provider": "local_daily_bar",
  "source_interface": "daily_bar",
  "warning": "实时行情不可用，使用本地最新真实日线。"
}
```

## Concrete Changes

### 1. Backend API

- Add `backend/app/api/quotes.py`.
- Register the router in the FastAPI app.
- Support `GET /api/quotes/{symbol}`.
- Optional: support `GET /api/quotes/search?q=...` backed by local `instrument` and cached data.

### 2. Quote Service

- Add `backend/app/services/quote_service.py`.
- Normalize symbol input such as `600519`, `600519.SH`, `sh600519`.
- Infer asset type using existing asset utilities where possible.
- Query realtime source first for A股 and ETF.
- Fallback to local `daily_bar` / `fund_nav`.
- Return explicit `MISSING` instead of throwing for normal data absence.

### 3. Real-only Boundary

- Real-time query success: `REAL_QUOTE`.
- Local true history fallback: `REAL_CACHED`.
- No true data: `MISSING`.
- Never return sample/mock/demo/estimated.

### 4. Frontend Types

- Add `QuoteResponse` type in `frontend/src/api/types.ts`.
- Optional helper in API client.

## Acceptance

- `GET /api/quotes/600519.SH` returns name, asset type, price and source when a real source or cache exists.
- `GET /api/quotes/510300.SH` supports ETF quote or local true cache.
- `GET /api/quotes/161725` returns fund latest true NAV from local `fund_nav` when available.
- Real-time source failure returns `REAL_CACHED` or `MISSING`, not sample.
- The API is read-only and does not mutate SQLite, Parquet, manifest or reports.
- Missing data is a normal response, not a 500.
- Backend compile, targeted smoke and frontend build pass.

## Verification

Suggested commands:

```bash
uv run python -m compileall backend/app worker scripts
PYTHONPATH=backend:. uv run python /tmp/quote_service_smoke.py
pnpm -C frontend build
git diff --check
```

Suggested smoke cases:

- Monkeypatch realtime success, confirm `REAL_QUOTE`.
- Monkeypatch realtime failure with local daily bar, confirm `REAL_CACHED`.
- Monkeypatch all sources missing, confirm `MISSING` and no exception.
- Confirm no new files are written under `data/`, `storage/`, or `reports/`.

## Notes

This service is for form assistance and portfolio valuation hints. It is not a trading quote engine and must not bypass the existing data credibility boundary used for investment advice.
