---
status: accepted
version: v1.0
created: 2026-06-24
updated: 2026-06-24
supersedes:
superseded_by:
owner: Codex
---

# 0003: Derive Positions On Read

## Decision

Positions are derived on read from `trade_record`.

The MVP does not maintain a persisted business position table, projection state machine, seed table, or fallback state.

## Context

Several alternatives were considered:

- Persist `portfolio_position` and update it in the same transaction as trade writes.
- Keep `portfolio_position_seed` for initial state.
- Use `portfolio_projection_state` with `PENDING / SUCCESS / FAILED`.
- Use async workers to rebuild position projection.

Those designs are useful at larger scale, but they add state and consistency surfaces. For this single-user MVP, they would create more risk than value.

## Consequences

Accepted:

- `GET /api/portfolio/positions` computes positions from `trade_record`.
- SELL validation uses local reduce scoped to `account_id + symbol`.
- Reduce order is always `trade_date, created_at, id`.
- `fee` is per trade event.
- Weighted average cost is the only MVP cost model.
- No trade means empty positions.

Rejected:

- Manual position writes.
- Seed / fallback positions.
- Projection status UI.
- Treating cache as business truth.

## Tradeoff

On-read reduce is simple and deterministic.

The cost is `O(n_symbol)` SELL validation and ledger-derived position query. This is acceptable for single-user low-to-medium-frequency usage. If future performance requires optimization, add a disposable read cache without changing the source of truth.
