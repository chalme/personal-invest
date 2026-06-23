---
status: accepted
version: v1.0
created: 2026-06-24
updated: 2026-06-24
supersedes:
superseded_by:
owner: Codex
---

# 0001: Use `trade_record` As The Only Source Of Truth

## Decision

`trade_record` is the only source of truth for trading behavior.

Positions, outcomes, summaries, and future caches must be derived from the ledger or from frozen decision anchors. They must not become competing business truth.

## Context

Earlier designs considered keeping `portfolio_position` as current state while also writing `trade_record`. That would create a hybrid model:

```text
trade_record + portfolio_position
```

Even if both are updated in one transaction, this is still a double-write system. Over time it can drift, require reconciliation, and make it unclear which table should be trusted.

The current project is a single-user MVP. Correctness and simplicity are more important than high-frequency write performance.

## Consequences

Accepted:

- `trade_record` is append-only through the normal API.
- Normal API does not update or delete historical trades.
- SELL validation is based on ledger-derived state.
- Position is an on-read projection, not a business write target.
- Future performance optimization may add a disposable read cache.

Rejected:

- Updating `portfolio_position` as part of the trade write path.
- Treating `portfolio_position` as current truth.
- Reconciliation between two business truth sources.

## Tradeoff

This choice keeps the architecture clean and avoids drift.

The cost is that SELL validation and position query require ledger reduce. For a single-user, low-to-medium-frequency system, local reduce scoped to `account_id + symbol` is acceptable.
