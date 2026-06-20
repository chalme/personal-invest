# P1-008: 拆分 advice_engine 并增加规则追溯

- Status: TODO
- Priority: P1
- Owner: Codex
- Created At: 2026-06-21
- Completed At:

## Goal

将投资建议生成从策略信号文件中拆出，并让每条建议能追溯规则版本、来源快照、上一建议等级和变化原因。

## Scope

- 新增 `backend/migrations/005_advice_rule_trace.sql`。
- 新增 `worker/advice/` 模块。
- 将建议生成、规则判断和写库逻辑从 `worker/strategy/signal_engine.py` 拆出。
- `investment_advice` 增加 `rule_code`、`rule_version`、`strategy_code`、`source_snapshot_type`、`source_snapshot_date`、`previous_advice_level`、`change_reason`。
- 预留 `rule_result` JSON 字段，用于保存系统调试和复盘所需的规则过程。

## Guardrails

- 第一版只搬迁结构和补追溯字段，不重写建议规则。
- 建议结果应尽量保持不变。
- AI 仍只解释规则生成的建议，不直接凭空生成买卖结论。

## Acceptance

- `generate_investment_advice` 的外部调用方式保持稳定。
- 每条建议可追溯规则版本、来源快照和数据日期。
- 每条建议能记录上一建议等级和变化原因。
- `key_metrics` 继续面向用户展示，`rule_result` 面向系统调试和复盘。

## Completion Markers

- Completed At:
- Changed Files:
- Verification:
- Notes:

