# Repository Guidelines

## Project Structure & Module Organization

This repository is a local personal-investing research system. Backend API code lives in `backend/app/`, with FastAPI entrypoint `backend/app/main.py` and service modules under `backend/app/services/`. Offline jobs and analytics live in `worker/`, grouped by domain such as `ingest/`, `factor/`, `portfolio/`, `report/`, and `review/`. Frontend code lives in `frontend/src/`, with pages in `frontend/src/pages/`, reusable UI in `frontend/src/components/`, API types/client code in `frontend/src/api/`, and global styles in `frontend/src/styles/`. Operational scripts are in `scripts/`, deployment units in `deploy/`, and product/architecture docs in `docs/`. Runtime data, logs, generated reports, and storage files belong in `data/`, `logs/`, `reports/`, and `storage/`.

## Build, Test, and Development Commands

- `make setup`: sync Python dependencies with `uv`, install frontend dependencies with `pnpm`, and initialize the database.
- `make dev`: start backend and frontend locally; logs go to `logs/backend.log` and `logs/frontend.log`.
- `make backend` / `make frontend`: run only one side of the app.
- `make init`: initialize local storage via `scripts/init_db.py`.
- `make daily`: run the daily worker job.
- `make check`: compile Python modules and run the frontend TypeScript/Vite build.
- `pnpm -C frontend build`: build the frontend directly.

## Coding Style & Naming Conventions

Python targets 3.11 and uses Ruff (`line-length = 100`, lint rules `E`, `F`, `I`, `UP`, `B`). Use four-space indentation, snake_case for modules/functions, and domain-focused module names matching existing packages. TypeScript uses strict mode, React JSX, PascalCase component/page files, and camelCase variables. Keep service logic in backend services and batch/data logic in worker modules.

## Testing Guidelines

There is no dedicated test suite yet. Before submitting changes, run `make check`. For future tests, place Python tests under `tests/` with `test_*.py` names, and keep frontend tests near the feature or under `frontend/src`. Cover service behavior, data-source fallbacks, and UI/API contract changes.

## Commit & Pull Request Guidelines

Recent history uses conventional prefixes such as `feat:`, `docs:`, and `fix:`. Keep commits scoped and imperative, for example `feat: add market provider fallback`. Pull requests should describe the change, list verification commands, link related docs/tasks when relevant, and include screenshots for UI changes.

## Security & Data Policy

Copy `.env.example` to `.env`; do not commit secrets, local databases, logs, or generated runtime files. Preserve the project’s real-only data policy: do not introduce mock, sample, demo, or estimated data as runtime fallbacks when real sources fail.
