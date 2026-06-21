# DATA-002: 真实数据源增强任务拆解

- Status: DONE
- Priority: P2
- Owner: Codex
- Created At: 2026-06-21
- Completed At: 2026-06-21

## Goal

把“真实数据源增强”拆成可以独立开发、独立验收的小任务，避免一次性接入过多外部数据源导致不可维护。

## Principles

- 先提升可信度可见性，再逐步提高真实数据覆盖率。
- 每个数据源任务必须输出统一 manifest，并明确 `source_mode`。
- `SAMPLE` 只能用于演示和兜底，不能驱动高置信建议。
- `ESTIMATED` 可以展示和低置信解释，不应单独触发高优先级事项。
- `REAL` 才能作为规则建议的重要输入。
- 真实数据失败时必须有 fallback 和页面提示，不允许静默降级。

## Split Tasks

### DATA-003: 行情日线稳定性增强

- Input: AKShare A 股、ETF、指数日线。
- Output: `daily_bar` Parquet + market manifest。
- source_mode: `REAL` / `SAMPLE` / `MIXED` / `MISSING`。
- Fallback: AKShare 失败时保留最近成功数据；无历史数据时才使用样本。
- Page Impact: Dashboard、市场页、股票页、ETF 页展示数据日期和来源。
- Advice Impact: 只有 `REAL` 或明确可接受的 `MIXED` 才能驱动高置信价格类建议。

### DATA-004: 交易日历与数据新鲜度

- Input: 交易日历或本地交易日推导。
- Output: `trading_calendar` 或 manifest 中的新鲜度判断。
- source_mode: `REAL` / `ESTIMATED`。
- Fallback: 无真实交易日历时按工作日估算，但必须标记 `ESTIMATED`。
- Page Impact: Dashboard 显示“是否为最近交易日数据”。
- Advice Impact: 数据过期时降低建议置信度，不触发高优先级事项。

### DATA-005: 股票真实财报源接入

- Input: 利润表、资产负债表、现金流量表。
- Output: `financial_statement_snapshot`、`financial_metric_snapshot`。
- source_mode: `REAL` / `MISSING`，不再用样本冒充真实财报。
- Fallback: 缺失时保留历史快照或显示缺失。
- Page Impact: 股票页财报模块显示真实数据日期和报告期。
- Advice Impact: 真实财报可影响公司质量和风险；缺失时只降级展示。

### DATA-006: 股票估值真实数据增强

- Input: PE、PB、PS、股息率、历史分位。
- Output: `valuation_snapshot`。
- source_mode: `REAL` / `ESTIMATED` / `MISSING`。
- Fallback: 历史分位无法获取时只展示当前估值，不生成分位结论。
- Page Impact: 股票页估值卡片区分当前估值和历史位置。
- Advice Impact: 估值真实数据可影响买入关注/减仓关注的置信度。

### DATA-007: 基金净值真实源稳定化

- Input: 场外基金单位净值、累计净值。
- Output: `fund_nav` Parquet + fund manifest。
- source_mode: `REAL` / `SAMPLE` / `MIXED` / `MISSING`。
- Fallback: AKShare 失败时保留最近成功净值，不用样本覆盖真实历史。
- Page Impact: 基金页展示净值数据来源和最新净值日期。
- Advice Impact: 只有真实净值可驱动基金收益/回撤高置信建议。

### DATA-008: 基金画像真实数据源

- Input: 基金类型、风险等级、经理、公司、规模、基准、费率。
- Output: `fund_profile`、`fund_manager_profile`、`fund_company_profile`。
- source_mode: `REAL` / `ESTIMATED` / `MISSING`。
- Fallback: 无画像时基金深度页面显示缺失，不套 ETF 或股票模型。
- Page Impact: 基金页深度画像区块从占位/估算升级为真实字段。
- Advice Impact: 真实基金类型和风险等级可影响持有体验与风险说明。

### DATA-009: ETF 跟踪指数与指数行情增强

- Input: ETF 跟踪指数代码、指数行情序列。
- Output: `etf_profile`、`etf_tracking_snapshot`。
- source_mode: `REAL` / `ESTIMATED` / `MISSING`。
- Fallback: 无指数序列时只展示跟踪方向，不生成跟踪误差结论。
- Page Impact: ETF 页展示指数名称、指数收益和跟踪质量来源。
- Advice Impact: 真实跟踪数据可触发 ETF 深度风险；估算只做提示。

### DATA-010: ETF 折溢价与规模增强

- Input: ETF 净值、IOPV、规模、成交额。
- Output: `etf_liquidity_snapshot`、`etf_tracking_snapshot`。
- source_mode: `REAL` / `ESTIMATED` / `MISSING`。
- Fallback: 缺少净值或 IOPV 时不计算确定性折溢价。
- Page Impact: ETF 页明确展示折溢价是否真实可用。
- Advice Impact: 真实大幅折溢价可进入风险事件；估算不能单独触发高优先级事项。

## Recommended Order

1. DATA-004：交易日历与数据新鲜度。
2. DATA-003：行情日线稳定性增强。
3. DATA-007：基金净值真实源稳定化。
4. DATA-005：股票真实财报源接入。
5. DATA-006：股票估值真实数据增强。
6. DATA-009：ETF 跟踪指数与指数行情增强。
7. DATA-010：ETF 折溢价与规模增强。
8. DATA-008：基金画像真实数据源。

## Verification

- `git diff --check`
- 每个子任务均包含输入、输出、source_mode、fallback、页面影响和建议规则影响。

## Notes

本任务只拆解，不接入新真实数据源。
