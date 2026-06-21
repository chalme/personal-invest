# DATA-011: 真实数据 Only 策略与 source mode 合约

- Status: TODO
- Priority: P0
- Owner: Codex
- Created At: 2026-06-21
- Completed At:

## Goal

建立全系统硬约束：线上和开发运行链路只允许真实数据或真实历史缓存；没有真实数据时必须显示 `MISSING` / 不可用，不能生成、写入、展示或用 sample/mock/demo/estimated 数据驱动投资判断。

## Scope

- 定义 runtime 可接受的数据状态：`REAL`、`REAL_CACHED` / `AKSHARE_CACHED`、`MISSING`、`STALE`。
- 废弃 runtime 正常路径中的 `SAMPLE`、`ESTIMATED`、`built_in_sample`、`deterministic_estimate`。
- 明确测试 fixture 与运行时数据的边界：测试可以有显式 fixture，但不能进入 worker、API、页面或本地开发数据目录。
- 统一数据可信度服务、manifest、worker、设置页、日报和页面文案的 source mode 语义。
- 为后续任务提供验收口径和 grep/audit 规则。

## Out of Scope

- 不接入新的付费数据源。
- 不保证所有资产都有真实数据。
- 不在本任务清理历史 sample 数据。
- 不直接重写股票、基金、ETF 分析模型。
- 不替代生产环境人工备份和数据清理授权。

## Concrete Changes

- 更新 `docs/data-pipeline.md`，加入 Real-only 数据策略、允许/禁止状态、fallback 决策表和页面降级规则。
- 更新 `docs/task-board.md` 当前主线，明确下一阶段优先处理真实数据 only。
- 在任务详情中定义所有后续任务必须满足的验收标准。
- 明确 `akshare_cached` 的语义：允许展示为真实历史缓存，但不能驱动高置信当日建议。
- 明确 `MISSING` 的语义：缺真实数据时的唯一合法兜底状态。

## Acceptance

- 文档明确：runtime 不允许新增 sample/mock/demo/estimated 数据。
- 文档明确：开发环境也不允许为了页面可看而自动造数据。
- 所有后续任务能按同一套 source mode 合约验收。
- `SAMPLE` / `ESTIMATED` 只允许作为历史污染告警或测试 fixture，不作为正常运行状态。

## Verification

- `git diff --check`
- 人工检查 `docs/data-pipeline.md` 是否包含允许状态、禁止状态、fallback 决策表。
- 人工检查 `docs/task-board.md` 是否把 `DATA-011` 到 `DATA-015` 纳入 Current Code Agent Tasks。

## Notes

本任务是治理入口，不直接改业务代码。核心取舍是牺牲演示完整性，换取投资数据可信度：宁可页面显示缺失，也不能造数据。
