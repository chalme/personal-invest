# PORT-004: 不同资产入口进入持仓录入

## Status

`DONE`

## Priority

`P1`

## Owner

`Codex`

## Goal

让股票页、ETF/基金页、观察池页进入持仓录入时自动携带 `asset_type` 和资产上下文，减少用户手动选择和输入，且避免类型误判。

## Why

`PORT-003` 解决的是统一持仓页里“先选类型再查询”。但更好的体验是：用户在明确上下文页面操作时，不需要再次思考资产类型。

例如：

```text
股票研究页点击“加入持仓” -> 默认 STOCK
ETF 研究页点击“加入持仓” -> 默认 ETF
场外基金页点击“加入持仓” -> 默认 FUND
观察池点击“加入持仓” -> 使用观察池已有 asset_type
```

这能同时保证体验和类型安全。

## Scope

涉及文件：

```text
frontend/src/App.tsx
frontend/src/pages/PortfolioPage.tsx
frontend/src/pages/WatchlistPage.tsx
frontend/src/pages/StocksPage.tsx
frontend/src/pages/FundsPage.tsx
optional frontend/src/api/types.ts
```

## Concrete Changes

### 1. 统一 prefill contract

前端页面跳转到持仓录入时，传递：

```ts
type PortfolioPrefill = {
  symbol: string;
  name?: string;
  asset_type: 'STOCK' | 'ETF' | 'FUND';
  reason?: string;
  source_page?: 'stocks' | 'funds' | 'watchlist' | 'etf';
};
```

### 2. PortfolioPage 使用 prefill

进入持仓页后：

```text
自动设置 asset_type
自动填 symbol/name
清空旧 quote
允许用户点击对应类型的“获取价格/净值”
```

### 3. 观察池一键加入持仓修正

观察池已有 `asset_type` 时，不再让后端猜类型；直接传入 `PortfolioPrefill.asset_type`。

### 4. 股票/基金/ETF 页面入口

在已有研究页或资产卡片中提供“加入持仓”动作，带入当前页面上下文。

第一版可以先覆盖：

```text
WatchlistPage -> PortfolioPage
StocksPage -> PortfolioPage
FundsPage -> PortfolioPage
```

ETF 如果当前与基金页共用，需要按资产类型区分 `ETF` / `FUND`。

## Out of Scope

- 不做交易流水。
- 不做券商导入。
- 不自动买入或自动下单。
- 不从页面动作自动删除观察池资产。
- 不自动运行每日任务。

## Acceptance

- 从观察池进入持仓录入时，`asset_type` 被保留并优先使用。
- 从股票页进入时，表单默认 `STOCK`。
- 从基金页进入时，场外基金默认 `FUND`，ETF 默认 `ETF`。
- 预填后点击查询会调用 `/api/quotes/{symbol}?asset_type=...`。
- 用户仍可手动修改类型，但修改类型后旧报价必须清空。

## Verification

```bash
pnpm -C frontend build
uv run python -m compileall backend/app worker scripts
git diff --check
```

人工页面检查：

```text
观察池 STOCK -> 持仓页默认股票
观察池 ETF -> 持仓页默认 ETF/场内基金
观察池 FUND -> 持仓页默认场外基金
股票页加入持仓 -> 默认 STOCK
基金页加入持仓 -> 保留 FUND 或 ETF 上下文
```

## Notes

这是对 `PORT-002` 的上下文增强。原则是：如果用户从一个已知资产类型的页面发起持仓录入，系统应继承该类型，而不是重新猜。

## Completion

- 观察池、股票页、基金/ETF 页进入持仓录入时会携带 asset_type 和上下文。
- Verification: py_compile, targeted ruff, typed quote smoke, frontend TypeScript, Vite build, git diff --check.
