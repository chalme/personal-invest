# P1-006: Fund Signals Reports AI

- Status: DONE
- Priority: P1
- Completed At: 2026-06-20

## Goal

Make signals, daily reports and local AI explanations cover both stocks and funds.

## Scope

- Generate FUND strategy signals from fund_analysis_snapshot.
- Add fund observation section to daily report.
- Include asset type in signal report lines.
- Add fund explanation endpoint and frontend AI mode.

## Changes

- worker/strategy/signal_engine.py
- worker/report/report_builder.py
- backend/app/services/ai_service.py
- backend/app/api/ai.py
- frontend/src/pages/AiAnalysisPage.tsx
- docs/task-board.md

## Acceptance

- FUND analysis can generate strategy_signal rows with asset_type FUND.
- Daily report includes fund observations.
- AI page can explain a fund by symbol.

## Verification

- scripts/init_db.py
- worker/daily_job.py
- make check
