# DOC-006: 收敛下一阶段执行看板

- Status: DONE
- Priority: P1
- Owner: Codex
- Created At: 2026-06-21
- Completed At: 2026-06-21

## Goal

把已经完成规划的真实数据源增强和关键页面结论化任务，正式提升为下一阶段 Code Agent 可执行任务。

## Scope

- 更新 `docs/task-board.md` 当前主线。
- 新增 `DATA-004`、`DATA-003`、`DATA-007`、`UX-002`、`UX-003`、`UX-004`、`UX-005` 为当前 TODO。
- 为每个任务创建独立详情页。
- 保留 Human Track，并明确人工任务不由 Code Agent 自动执行。

## Out of Scope

- 不实现代码。
- 不改页面。
- 不接入新数据源。
- 不执行线上人工验收。
- 不修改 Cloudflare、服务器、防火墙或 Secret 配置。

## Concrete Changes

- 下一阶段执行顺序固定为：`DATA-004 -> DATA-003 -> DATA-007 -> UX-002 -> UX-003 -> UX-004 -> UX-005`。
- 数据任务第一阶段继续基于 AKShare / 本地 fallback，不引入新付费供应商。
- 页面任务必须遵守数据可信度降级：`REAL` 可支撑高置信结论，`ESTIMATED` 只能低置信解释，`SAMPLE` 只做演示，`MISSING` 只展示缺失。

## Acceptance

- `docs/task-board.md` 中有清晰的下一阶段主线。
- 7 个下一阶段任务均在 Current Code Agent Tasks 中出现。
- 7 个下一阶段任务均有详情页。
- 每个任务都有状态、优先级、目标、范围、边界和验收标准。

## Verification

- `git diff --check`
- 搜索确认 `DATA-004`、`DATA-003`、`DATA-007`、`UX-002`、`UX-003`、`UX-004`、`UX-005` 出现在 `docs/task-board.md`。
- 搜索确认对应详情页存在并进入 Task Detail Index。

## Notes

本任务只做执行看板收敛，不改变业务代码。
