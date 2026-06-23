---
status: accepted
version: v1.0
created: 2026-06-24
updated: 2026-06-24
supersedes:
superseded_by:
owner: Codex
---

# 0002: Do Not Build Snapshot / Replay / Learning In The MVP

## Decision

The current MVP will not implement Snapshot, Replay, Learning, Attribution, or Behavior Scoring.

The MVP scope is:

```text
Trade -> Position -> Decision -> 7D Outcome
```

## Context

The long-term north star includes a Snapshot layer, where each decision can be tied to the world state visible at that time. That enables full replay and behavioral learning.

The current user constraint is different:

- Historical data is not important.
- The system has not started being used as the behavior ledger yet.
- The immediate goal is a working live system.

Adding Snapshot now would increase schema, worker, UI, and migration complexity before there is enough behavior data to learn from.

## Consequences

Accepted:

- No `decision_snapshot` or world-state snapshot in the MVP.
- No replay engine.
- No attribution model.
- No behavior scoring.
- No pattern mining or learning loop.
- Outcome only reports 7D feedback.

Rejected:

- Tying every decision to a time-machine snapshot in v1.
- Evaluating long-term decision quality in v1.
- Building a historical reconstruction system before the live ledger exists.

## Tradeoff

This makes the MVP much smaller and easier to ship.

The cost is that the system cannot yet answer: "What exact world did I see when I made this decision?" That is accepted for the current phase.
