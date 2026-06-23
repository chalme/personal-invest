---
status: current
version: v1.0
created: 2026-06-24
updated: 2026-06-24
supersedes:
superseded_by:
owner: Codex
---

# Decisions

This directory records accepted architecture decisions.

Each decision should explain one choice, the context behind it, the tradeoff, and the consequences. These documents are similar to ADRs.

Accepted decisions:

- [`0001-single-source-trade-ledger.md`](0001-single-source-trade-ledger.md): use `trade_record` as the only source of truth.
- [`0002-no-snapshot-in-mvp.md`](0002-no-snapshot-in-mvp.md): do not build Snapshot / Replay / Learning in the MVP.
- [`0003-on-read-position-projection.md`](0003-on-read-position-projection.md): derive positions on read from the trade ledger.
