# QUOTE-002: Typed Quote 查询

## Status

`TODO`

## Priority

`P0`

## Owner

`Codex`

## Goal

让报价接口显式接收资产类型，并按 `STOCK` / `ETF` / `FUND` 走不同真实数据链路，避免系统仅靠代码推断资产类型导致基金被误判为 ETF 或股票。

## Why

当前报价服务已经能提供只读报价辅助，但仍存在一个核心问题：

```text
用户输入 161725
  -> 后端 normalize_symbol 可能转成 161725.SZ
  -> infer_asset_type 可能推断成 ETF
  -> 场外基金被当成场内品种查询
```

投资系统里资产类型错误会污染后续持仓收益、风控、日报和复盘。第一版不应通过循环调用股票、ETF、基金多个实时源来猜类型，而应让调用方传入明确资产类型。

## Scope

涉及文件：

```text
backend/app/api/quotes.py
backend/app/services/quote_service.py
frontend/src/api/types.ts
```

## Concrete Changes

### 1. API 支持 asset_type 参数

当前：

```http
GET /api/quotes/{symbol}
```

扩展为：

```http
GET /api/quotes/{symbol}?asset_type=STOCK
GET /api/quotes/{symbol}?asset_type=ETF
GET /api/quotes/{symbol}?asset_type=FUND
```

要求：

```text
asset_type 可选，但持仓录入页必须传。
asset_type 只允许 STOCK / ETF / FUND。
用户显式传入的 asset_type 优先级高于代码推断。
```

### 2. QuoteService 改为 typed quote

新增或调整签名：

```python
def quote(self, raw_symbol: str, asset_type: str | None = None) -> dict[str, Any]:
    ...
```

优先级：

```text
1. 请求参数 asset_type
2. 本地 instrument.asset_type
3. 旧 infer_asset_type fallback
```

### 3. typed symbol normalization

资产类型决定 symbol 标准化策略：

```text
STOCK: 600519 -> 600519.SH, 000001 -> 000001.SZ
ETF:   510300 -> 510300.SH, 159919 -> 159919.SZ
FUND:  161725 -> 161725，不自动追加 .SZ / .SH
```

### 4. 按类型选择查询链路

```text
STOCK -> 股票实时行情 -> local daily_bar -> MISSING
ETF   -> ETF 实时行情 -> local daily_bar -> MISSING
FUND  -> local fund_nav -> MISSING
```

第一版 `FUND` 可以只使用本地 `fund_nav` 真实缓存；外部最新净值源放到 `QUOTE-003`。

### 5. 返回价格语义

返回结果增加或保证包含：

```text
symbol
name
asset_type
price
price_label
price_time
trade_date
source_mode
source_provider
source_interface
warning
```

`price_label` 规则：

| asset_type | price_label |
|---|---|
| `STOCK` | `当前价` |
| `ETF` | `交易价格` |
| `FUND` | `单位净值` |

## Out of Scope

- 不做自动资产类型识别服务。
- 不并发调用股票、ETF、基金接口猜类型。
- 不新增交易流水表。
- 不把手动价格写入 `daily_bar` 或 `fund_nav`。
- 不恢复 sample/mock/demo/estimated fallback。
- 不接 Tushare Pro 或付费数据源。

## Acceptance

- `GET /api/quotes/600519?asset_type=STOCK` 返回 `asset_type=STOCK`，并尝试股票报价链路。
- `GET /api/quotes/510300?asset_type=ETF` 返回 `asset_type=ETF`，并尝试 ETF 报价链路。
- `GET /api/quotes/161725?asset_type=FUND` 不能被规范成 `161725.SZ`，返回 `asset_type=FUND`。
- 实时源失败时返回 `REAL_CACHED` 或 `MISSING`，不生成 sample。
- 结果明确 `source_mode`、`source_provider`、`source_interface` 和 warning。

## Verification

```bash
PYTHONPATH=backend:. uv run python - <<'PY'
from app.services.quote_service import QuoteService

svc = QuoteService()
for symbol, asset_type in [
    ("600519", "STOCK"),
    ("510300", "ETF"),
    ("161725", "FUND"),
]:
    result = svc.quote(symbol, asset_type=asset_type)
    print(symbol, asset_type, result["symbol"], result["asset_type"], result["source_mode"])
PY

uv run python -m compileall backend/app worker scripts
pnpm -C frontend build
git diff --check
```

## Notes

本任务是对 `QUOTE-001` 的类型安全修正。核心原则是：用户或调用方选择的资产类型是主约束，系统不能用代码规则覆盖它。
