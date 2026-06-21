# DOC-004: 收敛产品 backlog 与长期路线图状态

- Status: TODO
- Priority: P1
- Owner: Codex
- Created At: 2026-06-21
- Completed At:

## Goal

把 `docs/product-backlog.md`、`docs/long-term-roadmap.md`、`docs/task-board.md` 与当前已实现能力对齐，避免已完成能力继续以未完成待办形式出现，影响后续任务判断。

## Scope

本任务只做文档状态收敛，不实现业务代码。

需要明确区分：

- 已完成能力。
- 当前真实短板。
- 未来 backlog。
- 已拆解并执行过的任务。

## Concrete Changes

- 更新 `docs/product-backlog.md`：
  - 将已完成的资产类型、模型收敛、股票财报 V1、场外基金深度 V1、ETF 深度 V1、复盘闭环、桌面端主题/密度从“待做主线”中移出。
  - 保留仍真实存在的产品打磨项，例如股票页研究结论化、持仓页组合决策化、日报投资简报化、真实数据源增强。
- 更新 `docs/long-term-roadmap.md`：
  - 把“当前短板”改为真实短板，不再包含已完成的迁移体系、`instrument`、ETF 独立口径、规则追溯、行业映射、组合快照。
  - 增加“已完成能力”小节，沉淀当前系统已具备的模型和闭环能力。
- 更新 `docs/task-board.md`：
  - 当前主线改为文档状态收敛与数据可信度总览。
  - 保持 `TODO` 只包含确认要执行的任务。

## Acceptance

- `product-backlog` 不再把已完成能力表达成未完成主线。
- `long-term-roadmap` 的当前短板不再包含已完成底座。
- `task-board` 当前主线与真实下一阶段一致。
- 下一阶段开发任务能从文档中清楚看出。
- 不修改业务代码。

## Verification

- `git diff --check`
- 搜索确认已完成能力不再以当前未完成主线表达。
- 搜索确认真实下一阶段仍包含数据可信度、真实数据源、产品页面打磨和运维安全。

## Notes

这是文档卫生任务。它不是线上人工验收，也不是新功能实现。
