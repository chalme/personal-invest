---
status: current
version: v1.6
created: 2026-06-24
updated: 2026-06-24
supersedes:
superseded_by:
owner: Codex
---

# Live Trading Behavior Recorder MVP

This is the current implementation baseline for the personal trading ledger.

## Summary

Build a single-user, minimal event-sourced trading ledger:

```text
Trade Ledger -> On-Read Position Projection -> Decision -> 7D Outcome
```

The system only records trade facts, derives current positions on read, records human decisions, and produces a simple 7-day delayed feedback result.

Out of scope:

- Snapshot.
- Replay.
- Learning.
- Attribution.
- Scoring.
- Seed / fallback state.
- Projection state machine.

## Core Principles

- `trade_record` is the only source of truth.
- Position is never written as business state.
- Position is always derived by `reduce(trade_record)`.
- SELL validation uses local ledger reduce scoped to `account_id + symbol`.
- Decision is frozen intent with a deterministic entry anchor.
- Outcome is 7D delayed evaluation only.
- This is a single-user, low-to-medium-frequency system; `O(n_symbol)` reduce is acceptable.

## Data Model

### `trade_record`

```text
id
account_id
symbol
trade_date
trade_type      BUY | SELL
quantity
price
fee
reason
created_at
```

Rules:

- Append-only.
- Normal API does not update or delete historical trades.
- `quantity > 0`.
- `price > 0`.
- `fee` is per trade event, not per unit.
- Index: `(account_id, symbol, trade_date, created_at, id)`.

### `decision_record`

```text
id
account_id
symbol
asset_type
decision_date
decision_type   BUY | SELL | HOLD
decision_reason
entry_price
entry_time
entry_price_date
entry_price_source
created_at
```

Rules:

- `decision_reason` is required.
- Entry anchor is frozen at creation time.
- The same `symbol + asset_type + decision_date` must reproduce the same entry anchor.
- `entry_price_source = LAST_CLOSE | FUND_NAV | CACHE_CLOSE | CACHE_NAV | MISSING`.

### `decision_outcome`

```text
decision_id
entry_price
price_7d
return_ratio
result          WIN | LOSS | FLAT | MISSING
computed_at
```

Rules:

- Generate `7D` only.
- Use frozen `decision_record.entry_price`.
- `result = WIN | LOSS | FLAT | MISSING`.

## Core Logic

### Ledger Reduce

Local position reduce:

```text
current_position = reduce(
  trade_record
  where account_id = ? and symbol = ?
  order by trade_date, created_at, id
)
```

Full account position query:

```text
positions = reduce(
  trade_record
  where account_id = ?
  group by symbol
  order by symbol, trade_date, created_at, id
)
```

When there are no trades, positions are empty.

### BUY

```text
new_qty = old_qty + quantity
new_avg_cost = (old_qty * old_avg_cost + quantity * price + fee) / new_qty
```

### SELL

Before writing a SELL, execute local reduce for `account_id + symbol`.

```text
if sell_quantity > current_quantity:
    reject trade
    do not insert
```

For a valid SELL:

```text
realized_pnl += (price - avg_cost) * sell_quantity - fee
quantity -= sell_quantity

if quantity == 0:
    position becomes empty
```

After a partial SELL:

```text
avg_cost unchanged
```

### Trade Write

```text
BEGIN
  validate quantity > 0
  validate price > 0
  if trade_type == SELL:
      reduce ledger by account_id + symbol
      reject if overflow
  insert trade_record
COMMIT
```

BUY does not require pre-reduce unless the API wants to return a projected preview.

### Entry Price

- Stock / ETF: use the latest available close before `decision_date`.
- Fund: use the latest available NAV before `decision_date`.
- Cache is allowed only if deterministic and versioned.
- If missing:

```text
entry_price = null
entry_price_source = MISSING
```

Freeze:

```text
entry_price
entry_price_date
entry_price_source
```

### Outcome

Calculate `7D` only:

```text
return_ratio = price_7d / entry_price - 1
```

Classification:

```text
WIN     if return_ratio > noise_band
LOSS    if return_ratio < -noise_band
FLAT    otherwise
MISSING if entry_price or price_7d is null
```

Noise band:

```text
stock / ETF: 0.005
fund:        0.003
```

## API Layer

Portfolio API:

```text
POST /api/portfolio/trades
GET  /api/portfolio/trades
GET  /api/portfolio/positions
```

Review API:

```text
POST /api/review/decisions
GET  /api/review/decisions
GET  /api/review/outcomes
```

Behavior rules:

- Trade write success means the trade was inserted.
- Position query is on-read reduce.
- No position write path.
- No projection status.
- No seed / fallback state.

## Worker System

`outcome_worker`:

```text
input:  decision_record
output: due 7D decision_outcome
```

`daily_job`:

```text
compute overdue outcomes
```

No position worker is required.

## UI Contract

- No trades means empty positions.
- The Portfolio page shows on-read derived positions.
- Do not show `PENDING / SUCCESS / FAILED` projection state.
- Do not allow manual editing of positions.
- SELL overflow is shown as a trade input error.
- Missing real price / NAV is shown as `MISSING`; do not fill with fake data.

## Test Plan

Trade:

- BUY inserts successfully.
- BUY then position query derives the correct holding.
- Multiple BUY trades produce correct weighted average cost, with fee included in cost.
- SELL validation reads only the current `account_id + symbol` ledger.
- SELL overflow is rejected and not inserted.
- Valid SELL keeps `avg_cost` unchanged and deducts fee from `realized_pnl`.
- Full exit removes the active position from position query.

Decision:

- Empty `decision_reason` is rejected.
- Entry anchor is frozen at creation time.
- The same `symbol + asset_type + decision_date` reproduces the same entry anchor.

Outcome:

- Due `7D` outcome is generated.
- `noise_band` is applied correctly.
- Missing entry or measurement price returns `MISSING`.

Verification:

- Run `make check`.

## Assumptions

- Single-user system with low-to-medium trade frequency.
- Old data can be discarded; no migration compatibility is required for this MVP.
- `trade_record` is the only source of truth.
- Position is a ledger-derived view.
- Weighted average cost is the only MVP cost model.
- `fee` is per trade event.
- Future performance optimization may add a disposable read cache, but it must not change the source of truth.
- No Snapshot / Replay / Learning / Attribution / Scoring.
- No seed / fallback state.
- Missing real data is shown as missing; do not use mock, demo, sample, or estimate.

## Final Statement

This is a minimal event-sourced trading ledger with on-read position projection, frozen decision anchors, and delayed 7D outcome feedback.
