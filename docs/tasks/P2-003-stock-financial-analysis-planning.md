# P2-003: 股票财报分析规划

- Status: TODO
- Priority: P2
- Owner: Codex
- Created At: 2026-06-21
- Completed At:

## Goal

为 `STOCK` 设计财报数据、财务指标、估值、财报事件和股票质量分析口径，让股票分析能解释公司质量、财报趋势、现金流、负债、ROE 和估值位置。

## Scope

本任务只产出设计规划，不实现数据库、worker、API 或前端代码。规划交付物是 `docs/stock-financial-analysis-design.md`。

## Concrete Changes

- 设计财报数据模型：利润表、资产负债表、现金流量表、分红和回购。
- 设计财务指标口径：营收增速、净利润增速、毛利率、净利率、ROE、ROA、负债率、经营现金流和自由现金流。
- 设计估值口径：PE、PB、PS、股息率、历史分位、行业分位和估值区间。
- 设计财报事件：业绩预告、定期报告、利润大幅变化、现金流异常、资产减值、审计意见和管理层变化。
- 规划 worker 流程、API 范围、页面范围、`risk_event` 接入点、`review_task` 接入点、日报接入点和 AI 解释边界。
- 规划如何避免样本数据或缺失数据被误判为真实财报结论。

## Acceptance

- 明确该能力只适用于 `STOCK`。
- ETF、LOF、FUND 不使用股票财报、公司估值或公司质量评分。
- 股票基本面评分可追溯到财务指标、数据日期和数据来源。
- 财报异常能进入 `risk_event`、`review_task`、日报和 AI 解释链路。
- AI 只解释财报变化和评分依据，不直接根据财报自由生成买卖建议。

## Verification

- 设计文档能回答财报数据存哪里、指标怎么算、估值怎么解释、财报事件怎么识别、公司质量评分怎么追溯。
- `rtk git diff --check`。

## Notes

- 股票看公司。
- 本任务完成后，再拆股票财报分析 V1 的具体实现任务。
