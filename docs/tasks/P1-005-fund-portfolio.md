# P1-005: Fund Portfolio Support

- Status: DONE
- Priority: P1
- Completed At: 2026-06-20

## Goal

Allow FUND assets to participate in portfolio overview, valuation and risk checks.

## Scope

- Use latest fund NAV for FUND positions when available.
- Attach fund analysis snapshot to FUND positions.
- Add FUND-specific weak score risk event.
- Update portfolio UI copy for shares, cost NAV and current NAV.

## Changes

- backend/app/services/portfolio_service.py
- worker/risk/risk_engine.py
- frontend/src/pages/PortfolioPage.tsx
- frontend/src/api/types.ts
- docs/task-board.md

## Acceptance

- FUND positions show market value, PnL and score.
- FUND positions can use latest fund_nav as current price source.
- Risk engine distinguishes FUND weak score from STOCK weak score.

## Verification

- scripts/init_db.py
- make daily
- make check
