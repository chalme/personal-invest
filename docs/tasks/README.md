# Task Details

本目录用于保存复杂任务的详情页。简单任务只记录在 `docs/task-board.md`。

## When To Create A Detail Page

满足任一条件时，为任务创建详情页：

- 涉及数据库 schema 或迁移。
- 涉及前后端、worker 多处联动。
- 需要明确数据口径、边界、回滚方式或验收步骤。
- 任务预计会跨多个提交或多个工作日。

## Naming

文件名格式：

```text
{task-id}-{slug}.md
```

示例：

- `P0-003-asset-type.md`
- `P1-001-fund-data-pipeline.md`
- `P1-002-fund-analysis.md`

## Template

```markdown
# TASK-ID: Title

- Status: TODO
- Priority: P0/P1/P2
- Owner: Codex
- Created At: YYYY-MM-DD
- Completed At:

## Goal

## Scope

## Concrete Changes

## Acceptance

## Verification

## Notes
```
