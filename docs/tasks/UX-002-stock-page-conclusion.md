# UX-002: 股票页研究结论化

- Status: DONE
- Priority: P2
- Owner: Codex
- Created At: 2026-06-21
- Completed At: 2026-06-21

## Goal

将股票页从指标展示页升级为研究结论页，首屏回答：这家公司是否值得继续观察、为什么、下一步看什么。

## Scope

- 增加顶部研究结论卡。
- 展示建议等级、一句话结论、置信度、数据日期和 source mode。
- 把趋势、估值、公司质量、行业和财报事件组织成关键证据。
- 把财报异常、估值偏高、趋势转弱、行业转弱组织成风险点。
- 保留明细图表和指标表作为下层内容。

## Out of Scope

- 不做移动端专项。
- 不新增复杂图表。
- 不改变股票分析规则。
- 不让 AI 生成黑盒高置信建议。

## Concrete Changes

- 股票页首屏先给结论，再给证据。
- `REAL` 数据可支撑高置信结论。
- `ESTIMATED` 估值必须显示“估算”。
- `SAMPLE` 财报不展示高置信公司质量结论。
- `MISSING` 财报只展示缺失，不生成基本面判断。

## Acceptance

- 用户不用读完整表格，也能知道该股票当前结论、证据、风险和下一步观察。
- 页面明确区分事实、判断、风险和动作。
- 数据可信度降级文案清楚，不把样本/估算包装成真实结论。

## Verification

- `pnpm -C frontend build`
- 检查有财报、估算财报、样本财报、缺失财报四类展示。
- 检查股票页在无数据时有明确空态。
- `git diff --check`

## Completed Changes

- 股票页首屏新增“研究结论”卡。
- 结论卡展示当前判断、建议状态、置信度、数据日期、数据来源和下一步观察。
- 将趋势、估值、公司质量、行业和资金组织为关键证据。
- 将结构化风险、财报边界和高风险分组织为风险边界。
- `SAMPLE` / `MISSING` / `ESTIMATED` / `MIXED` 数据源会降低置信度或提示降级使用，不包装成真实高置信结论。

## Verification Result

- Passed: `git diff --check`
- Passed: `uv run python -m compileall backend/app worker scripts`
- Not run: `pnpm -C frontend build`，当前执行环境缺少 `node` / `pnpm`。

## Notes

页面优化从股票页开始，但不做全站 redesign。本任务只改前端信息结构，不改变股票分析规则和后端数据模型。
