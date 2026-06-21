# PORT-003: 持仓录入先选类型再查询

## Status

`DONE`

## Priority

`P0`

## Owner

`Codex`

## Goal

把持仓录入从“输入代码后系统猜资产类型”调整为“用户先选资产类型，再按类型获取价格或净值”，降低误判风险并提升录入稳定性。

## Why

当前持仓录入已经支持“获取真实报价”，但如果报价接口不接收资产类型，后端仍会按代码规则推断。对于 `161725` 这类基金代码，系统可能误判为 `ETF` 或场内品种。

更稳的交互是：

```text
用户选择资产类型
  -> 股票 / ETF / 场外基金
用户填写代码
  -> 系统只调用该类型对应数据链路
```

这比循环实时调用多个接口猜类型更快、更稳定，也更符合投资数据安全边界。

## Scope

涉及文件：

```text
frontend/src/pages/PortfolioPage.tsx
frontend/src/api/types.ts
optional frontend/src/App.tsx
```

## Concrete Changes

### 1. 表单顺序调整

当前表单应调整为：

```text
1. 资产类型
2. 资产代码
3. 获取价格/净值
4. 名称
5. 数量/份额
6. 成本价/成本净值
7. 止损 / 止盈 / 理由
8. 保存前影响预览
```

### 2. 查询请求带 asset_type

当前：

```text
GET /api/quotes/{symbol}
```

调整为：

```text
GET /api/quotes/{symbol}?asset_type=${form.asset_type}
```

### 3. 按类型变更按钮与字段文案

| asset_type | 查询按钮 | 价格字段 | 成本字段 | 数量字段 |
|---|---|---|---|---|
| `STOCK` | `获取实时价格` | `当前价` | `成本价` | `数量` |
| `ETF` | `获取交易价格` | `交易价格` | `成本价` | `份额` |
| `FUND` | `获取最新净值` | `单位净值` | `成本净值` | `份额` |

### 4. 切换类型时清空旧报价

当用户切换 `asset_type` 时，必须清空：

```text
quote
quote error
manual price state
自动填充的 current_price 来源提示
```

避免用户先查了股票价格，再切成基金但旧价格仍保留。

### 5. 状态文案拆分

至少支持：

```text
尚未获取报价/净值
正在获取
已获取实时真实报价
已使用本地真实缓存
未找到真实价格/净值，可手动录入临时价格
```

`FUND` 文案不能叫“实时价格”，应叫“最新净值”。

## Out of Scope

- 不做资产自动识别候选列表。
- 不做多接口循环探测类型。
- 不新增交易流水表。
- 不做批量导入或券商导入。
- 不把手动价格写入行情或净值数据源。

## Acceptance

- 用户添加持仓前必须能明确选择 `股票` / `ETF/场内基金` / `场外基金`。
- 点击获取时请求 URL 带 `asset_type`。
- `FUND + 161725` 不会在前端展示为 `161725.SZ`。
- 按类型显示不同字段文案和按钮文案。
- 切换类型后旧报价被清空。
- `MISSING` 时仍允许手动录入临时价格，但提示该价格仅用于持仓快照估算。

## Verification

```bash
pnpm -C frontend build
uv run python -m compileall backend/app worker scripts
git diff --check
```

人工页面检查：

```text
股票 + 600519 -> 查询按钮为“获取实时价格”
ETF + 510300 -> 查询按钮为“获取交易价格”
场外基金 + 161725 -> 查询按钮为“获取最新净值”
切换类型后报价卡清空
```

## Notes

这是 `PORT-001` 的安全性修正：持仓录入可以低摩擦，但不能为了少一步选择而误判资产类型。

## Completion

- 持仓录入已改为先选资产类型再查询，并按类型切换按钮、字段文案和旧报价清空逻辑。
- Verification: py_compile, targeted ruff, typed quote smoke, frontend TypeScript, Vite build, git diff --check.
