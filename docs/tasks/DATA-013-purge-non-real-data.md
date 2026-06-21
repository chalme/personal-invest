# DATA-013: 历史 sample / estimated 数据审计与清理脚本

- Status: TODO
- Priority: P0
- Owner: Codex
- Created At: 2026-06-21
- Completed At:

## Goal

提供可重复、默认 dry-run 的清理工具，审计并清理当前 SQLite 与 Parquet 中已经存在的 sample / estimated / built-in fake 数据，让页面不再继续读取历史污染数据。

## Scope

- 新增脚本，例如 `scripts/audit_real_only.py` 和 `scripts/purge_non_real_data.py`。
- 审计 Parquet：`data/parquet/daily_bar`、`data/parquet/fund_nav` 等带 `source` 字段的数据集。
- 审计 SQLite：股票财务、估值、质量、基金画像、基金基准/同类/持仓暴露、ETF 深度分析相关表。
- 清理 source/source_mode 属于 `sample`、`SAMPLE`、`estimated`、`ESTIMATED`、`built_in_sample`、`deterministic_estimate` 的记录。
- 清理后触发或提示重新生成可信度 manifest，让页面显示 `MISSING` 而不是历史 sample。

## Out of Scope

- 不直接操作生产环境数据库。
- 不绕过备份直接删除数据。
- 不删除真实历史缓存 `akshare_cached`。
- 不接入新真实数据源补齐缺口。
- 不做 UI 清理按钮。

## Concrete Changes

- 审计脚本输出每个表/数据集的非真实记录数量、source 分布和建议动作。
- 清理脚本默认 dry-run，只有显式 `--apply` 才执行删除或重写。
- 清理脚本执行前检查备份提示，推荐先运行 `scripts/backup.sh`。
- Parquet 清理采用重写过滤后的数据集，不保留 source 为 sample/estimated 的行。
- SQLite 清理使用事务，失败必须回滚。
- 清理后输出摘要：删除行数、剩余真实行数、变为 MISSING 的模块。

## Acceptance

- dry-run 能列出当前所有 sample / estimated 污染来源和数量。
- `--apply` 后业务数据集中不再有 sample / estimated runtime 记录。
- 清理不会删除 `akshare`、`akshare_cached` 或其他真实来源记录。
- 清理后 Dashboard / Settings 应显示真实、真实缓存、缺失或过期，不再显示当前历史 sample 正常态。
- 脚本可重复执行，第二次执行不会误删真实数据。

## Verification

- `uv run python -m compileall backend/app worker scripts`
- `uv run python scripts/audit_real_only.py`
- 在临时复制的数据目录/数据库上执行 `uv run python scripts/purge_non_real_data.py --apply`。
- 重复执行清理脚本，确认幂等。
- SQLite 查询确认目标表没有 `SAMPLE` / `ESTIMATED` source_mode。
- Parquet 读取确认 `source` 不包含 `sample` / `estimated`。
- `git diff --check`

## Notes

本任务风险高于普通页面任务。必须默认 dry-run、事务化、可重复，并且不能在没有备份的情况下静默删除数据。生产清理执行仍需要人工确认。
