# P1-004: Observation Pool

- Status: DONE
- Priority: P1
- Completed At: 2026-06-20

## Goal

Upgrade watchlist into an observation pool for STOCK, ETF and FUND assets.

## Scope

- Add asset type filter.
- Rename UI copy from watchlist/self-selected stocks to observation pool.
- Keep asset type selection in create/update form.
- Allow backend list API to filter by asset type.

## Changes

- backend/app/api/watchlist.py
- backend/app/services/watchlist_service.py
- frontend/src/pages/WatchlistPage.tsx
- frontend/src/components/layout/AppLayout.tsx
- frontend/src/styles/global.css

## Acceptance

- Users can add FUND assets.
- Users can filter by STOCK, ETF and FUND.
- UI no longer treats every observed asset as a stock.

## Verification

- make check
