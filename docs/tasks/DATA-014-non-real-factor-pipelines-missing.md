# DATA-014: 股票 / 基金 / ETF 非真实因子改为 MISSING

- Status: TODO
- Priority: P1
- Owner: Codex
- Created At: 2026-06-21
- Completed At:

## Goal

停止股票财务、基金画像、基金基准/同类/持仓暴露、ETF 深度分析中的内置样本和确定性估算生成。没有真实源时写入缺失状态或跳过快照，让分析、日报、建议和页面都明确显示“真实数据未接入”。

## Scope

- 股票财务与估值：`worker/factor/stock_financial.py`。
- 基金画像：`worker/fund/deep_profile.py`。
- 基金基准、同类排名、持仓暴露：`worker/fund/benchmark_peer.py`。
- ETF 深度分析相关 worker：ETF 画像、流动性、风险收益、跟踪误差、折溢价等现有实现文件。
- 后端服务和页面读取逻辑需要能处理缺失快照，不报错、不伪造结论。

## Out of Scope

- 不接入新的真实财报源、基金画像源或 ETF 数据源。
- 不删除历史污染数据，历史清理由 `DATA-013` 负责。
- 不重构完整分析模型。
- 不做外部 API key 配置 UI。

## Concrete Changes

- 移除 runtime 对 `SAMPLE_PROFILES`、`built_in_sample`、`deterministic_estimate` 等非真实生成逻辑的依赖。
- 没有真实输入时，不写假快照；必要时写入明确的 `MISSING` 状态记录或由服务层返回缺失说明。
- 调整分析 worker：缺真实数据时输出 warning，不让 daily job 失败。
- 调整后端服务：快照缺失时返回空态/缺失态，而不是异常或默认分数。
- 调整建议/日报：缺真实因子不能驱动高置信建议，只能提示数据缺口。

## Acceptance

- 新运行的股票财务/估值/质量 worker 不再产生 `SAMPLE` 或 `ESTIMATED` 快照。
- 新运行的基金画像/基准/同类/暴露 worker 不再产生 sample 内容，例如样本基金公司、样本经理、样本暴露。
- 新运行的 ETF 深度分析 worker 不再产生 estimated 作为正常分析结论。
- 页面和 API 对缺失快照稳定返回，不崩溃、不显示假评分。
- 日报和建议能明确说明真实数据缺失，不能把缺失模块包装成分析结论。

## Verification

- `uv run python -m compileall backend/app worker scripts`
- 针对无真实输入的股票、基金、ETF 运行对应 worker smoke test。
- SQLite 查询确认本次运行没有新增 `SAMPLE` / `ESTIMATED` source_mode。
- API smoke test 确认股票页、基金页、ETF 相关接口缺失数据时返回稳定结构。
- `pnpm -C frontend build`
- `git diff --check`

## Notes

本任务会让部分页面从“看起来很完整”变成“真实数据缺失”。这是符合真实数据 only 的正确结果。
