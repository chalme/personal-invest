# QUOTE-004: 实时报价真实源 fallback 策略标准化

## Status

`TODO`

## Priority

`P0`

## Owner

`Codex`

## Goal

让持仓录入的“获取价格 / 净值”具备清晰的真实源 fallback 策略：东财实时接口不可用时，按资产类型尝试真实备用源或本地真实缓存；全部失败才返回 `MISSING`。不通过循环调用多个源来猜资产类型。

## Background

当前报价服务已经有第一版 `GET /api/quotes/{symbol}`，但存在两个主要问题：

- 股票、ETF、场外基金没有完全按 `asset_type` 分链路查询。
- 实时源失败后 fallback 语义需要更明确，尤其是东财实时接口不稳定时，用户不应直接看到“只能手动录入”，而是先尝试同类型真实备用源或本地真实缓存。

本任务依赖 `QUOTE-002` 的 typed quote query，即前端必须传入用户或上下文确认后的 `asset_type`。

## Provider Chain

### STOCK

```text
AKShare Eastmoney stock_zh_a_spot_em
  -> optional easyquotation sina/tencent
  -> local daily_bar REAL_CACHED
  -> MISSING
```

### ETF

```text
AKShare Eastmoney fund_etf_spot_em
  -> optional compatible quote source
  -> local daily_bar REAL_CACHED
  -> MISSING
```

### FUND

```text
latest published NAV provider
  -> local fund_nav REAL_CACHED
  -> MISSING
```

场外基金不显示“实时价格”，只显示“最新单位净值 / 最新公布净值”。

## Scope

- Extend `backend/app/services/quote_service.py` to support typed provider chains.
- Ensure `backend/app/api/quotes.py` accepts and validates `asset_type`.
- Return provider attempt metadata where practical: selected provider, interface, fallback reason, source mode and warning.
- Add ETF real quote path using `fund_etf_spot_em()`.
- Ensure FUND path never normalizes `161725` into `161725.SZ`.
- Keep local cache fallback read-only; do not write realtime quotes into `daily_bar` or `fund_nav`.

## Out of Scope

- 不自动识别资产类型。
- 不并发调用股票、ETF、基金接口来猜类型。
- 不新增交易流水表。
- 不把手动价格写入行情或净值历史表。
- 不引入付费数据源。
- 不恢复 sample/mock/demo/estimated fallback。

## API Contract

Request:

```http
GET /api/quotes/600519?asset_type=STOCK
GET /api/quotes/510300?asset_type=ETF
GET /api/quotes/161725?asset_type=FUND
```

Response shape:

```json
{
  "data": {
    "symbol": "600519.SH",
    "name": "贵州茅台",
    "asset_type": "STOCK",
    "price": 1215.0,
    "price_label": "当前价",
    "price_time": null,
    "trade_date": "2026-06-18",
    "source_mode": "REAL_CACHED",
    "source_provider": "local_daily_bar",
    "source_interface": "daily_bar",
    "fallback_reason": "realtime_provider_unavailable",
    "warning": "实时源不可用，已使用本地最新真实历史缓存；不代表盘中实时价格。"
  }
}
```

## UI Contract

`PortfolioPage` should present different wording by type:

| asset_type | Button | Price label |
|---|---|---|
| `STOCK` | 获取实时价格 | 当前价 |
| `ETF` | 获取交易价格 | 交易价格 |
| `FUND` | 获取最新净值 | 单位净值 |

When source mode is `MISSING`, UI may allow manual temporary price, but must label it as a portfolio snapshot estimate only.

## Acceptance Criteria

- `STOCK + 600519` first tries stock realtime provider, then local `daily_bar`, then `MISSING`.
- `ETF + 510300` first tries ETF realtime provider `fund_etf_spot_em()`, not stock spot provider.
- `FUND + 161725` queries latest NAV / local `fund_nav`; it must not become `161725.SZ`.
- Response includes `source_provider`, `source_interface`, `fallback_reason` or equivalent warning.
- Realtime quote failures are bounded by timeout and do not block the whole page indefinitely.
- Manual price remains local to `portfolio_position.current_price`; it is not written to quote/history datasets.

## Verification

```bash
git diff --check
uv run python -m compileall backend/app
PYTHONPATH=backend:. uv run python - <<'PY'
from app.services.quote_service import QuoteService

svc = QuoteService()
for symbol, asset_type in [
    ("600519", "STOCK"),
    ("510300", "ETF"),
    ("161725", "FUND"),
]:
    result = svc.quote(symbol, asset_type=asset_type)
    print(symbol, asset_type, result["asset_type"], result["symbol"], result["source_mode"])
PY
pnpm -C frontend build
```

## Notes

- 本任务是报价层 fallback，不替代 `DATA-023` 的历史行情同步 fallback。
- 第一版可以不引入新依赖；如果引入 `easyquotation`，必须单独评估依赖体积、维护状态、字段稳定性和超时控制。

