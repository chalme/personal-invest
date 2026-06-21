# QUOTE-003: 场外基金最新净值真实源增强

## Status

`TODO`

## Priority

`P1`

## Owner

`Codex`

## Goal

增强 `FUND` 报价链路，让场外基金持仓录入可以获取最新公布单位净值；外部真实源不可用时再降级到本地 `fund_nav` 真实缓存或 `MISSING`。

## Why

场外基金没有场内实时交易价格。它的价格语义应该是：

```text
最新公布单位净值 / 最新历史净值
```

当前第一版报价链路可以优先依赖本地 `fund_nav`，但如果用户新增基金持仓时本地还没有同步该基金净值，体验仍然会进入 `MISSING`。本任务补强按需查询最新净值的真实源。

## Scope

涉及文件：

```text
backend/app/services/quote_service.py
backend/app/api/quotes.py
optional scripts/probe_market_sources.py
```

## Concrete Changes

### 1. FUND 查询链路增强

目标链路：

```text
FUND
  -> 外部真实基金净值源
  -> local fund_nav
  -> MISSING
```

可选外部源：

```text
ak.fund_open_fund_info_em(symbol=code, indicator="单位净值走势")
```

第一版只需要读取最新一行，返回：

```text
单位净值
净值日期
日增长率，若可用
```

### 2. 明确 source 语义

外部源成功：

```text
source_mode = REAL_QUOTE
source_provider = eastmoney_ttfund
source_interface = fund_open_fund_info_em
price_label = 单位净值
```

本地缓存成功：

```text
source_mode = REAL_CACHED
source_provider = local_fund_nav
source_interface = fund_nav
price_label = 单位净值
```

### 3. timeout 与失败处理

基金净值接口可能较慢。要求：

```text
单次调用必须有 timeout。
失败不能卡死报价接口。
失败后降级本地 fund_nav。
最终缺失返回 MISSING。
```

### 4. 不写入 fund_nav

本任务是只读报价增强，不应把按需查到的净值直接写入 `data/parquet/fund_nav`。

如果后续要缓存，需要单独任务设计 `quote_cache`，不能污染历史净值数据集。

## Out of Scope

- 不做基金估算净值。
- 不做场外基金实时价格。
- 不写 `fund_nav`。
- 不新增基金画像或基金经理信息。
- 不接 Tushare Pro 或付费数据源。
- 不恢复 sample/mock/demo/estimated。

## Acceptance

- `GET /api/quotes/161725?asset_type=FUND` 不被转成 `161725.SZ`。
- 外部基金净值源可用时返回 `REAL_QUOTE` 和最新单位净值。
- 外部基金净值源不可用但本地 `fund_nav` 存在时返回 `REAL_CACHED`。
- 全部失败时返回 `MISSING` 和明确 warning。
- 不写入 `fund_nav`、`daily_bar` 或 manifest。

## Verification

```bash
PYTHONPATH=backend:. uv run --extra data python - <<'PY'
from app.services.quote_service import QuoteService

result = QuoteService().quote("161725", asset_type="FUND")
print(result)
assert result["asset_type"] == "FUND"
assert not result["symbol"].endswith(".SZ")
PY

uv run python -m compileall backend/app worker scripts
git diff --check
```

## Notes

场外基金报价在页面上应展示为“最新净值”或“单位净值”，不能展示为“实时价格”。
