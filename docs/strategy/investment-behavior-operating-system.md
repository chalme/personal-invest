---
status: accepted
version: v1.0
created: 2026-06-24
updated: 2026-06-24
supersedes:
superseded_by:
owner: Codex
---

# 投资行为操作系统总体规划

本文记录 Personal Invest 的长期北极星。它不是当前 MVP 的实现规格；当前实现以 [`../specs/trading-ledger-mvp-v1.6.md`](../specs/trading-ledger-mvp-v1.6.md) 为准。

## 系统本质

长期目标是构建一个可回放的个人投资行为记录系统，用于分析投资者如何做决策，而不是替代投资者做决策。

压缩成一句话：

```text
记录当时看到的世界、当时做出的选择、以及后来发生的结果。
```

## 10 层事实架构

```text
L10 Insight Layer
    模式识别 / 风险扫描 / 机会发现
    只做提示，不做决策

L9 Outcome Layer
    决策结果追踪
    PnL + 结果反馈

L8 Decision Layer
    人类决策记录
    action + reason + thesis + invalidation

L7 Snapshot Layer
    时间快照
    记录当时看到的 market / portfolio / risk state

L6 Holding Layer
    当前持仓
    由事实源计算得到

L5 Trade Ledger
    BUY / SELL / DIVIDEND / CASHFLOW
    唯一事实源，原则上不可变

L4 Data Ingestion Layer
    AKShare / BaoStock / Tencent 等真实数据源接入
    normalize / validate / cache

L3 External Data Layer
    行情 / 基金 / 财报 / 指数

L2 System Interface
    Dashboard / API / Jobs

L1 User Interface
    今日工作台 / 持仓 / 复盘 / 报告
```

## 长期收敛原则

1. `Trade` 是唯一事实源。
2. `Snapshot` 是时间机器；没有 Snapshot，就无法做完整回放。
3. `Decision` 必须带理由；没有 reason 的决策数据不可用于复盘。
4. `Outcome` 是反馈层；它回答后来发生了什么。
5. `Insight` 只能提示，不能参与或替代决策。
6. 缺真实数据时必须显示 `MISSING`，不能用 mock / sample / demo / estimate 补齐。

## 当前阶段降维

当前系统先做轻量 Live System，而不是完整行为学习系统。

当前 MVP 链路：

```text
Trade -> Position -> Decision -> Outcome
```

已明确不进入当前 MVP：

- Snapshot。
- Replay。
- Attribution。
- Behavior scoring。
- Learning / pattern mining。
- Seed / fallback position。
- Projection state machine。

当前冻结实现是：

```text
Trade Ledger -> On-Read Position Projection -> Decision -> 7D Outcome
```

这意味着：

- `trade_record` 是唯一事实源。
- 持仓是 `reduce(trade_record)` 的派生视图。
- Decision 必须有 reason，并冻结 deterministic entry anchor。
- Outcome 只做 7D feedback。
- Insight / Signal / Advice 只提供提示，不做自动决策。

## 阶段关系

### 当前阶段：轻量交易行为记录系统

目标：

- 记录未来交易事实。
- 实时派生当前持仓。
- 记录为什么做决策。
- 在 7 天后给出简单反馈。

适合：

- 单人使用。
- 低到中频交易。
- 先跑起来，先形成行为记录习惯。

### 后续阶段：复盘增强

只有当轻量账本稳定使用后，才考虑补充：

- 更长 outcome 窗口，例如 30D / 90D。
- 决策 thesis / invalidation。
- 决策与建议、风险事件的关联。
- 更完整的持仓暴露解释。

### 远期阶段：行为操作系统

只有当决策记录和 outcome 有足够真实样本后，才考虑：

- Snapshot 时间机器。
- 行为模式分析。
- 决策质量复盘。
- 风险偏好漂移识别。
- 长期策略学习。

## 关键边界

- 当前系统不是自动交易系统。
- 当前系统不是 AI 投资顾问。
- 当前系统不是完整学习系统。
- AI 只能解释已有数据、规则和记录，不能直接下单或替代人工判断。
- Insight / Signal / Advice 是提醒，不是 action。
