#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

source "$ROOT_DIR/scripts/lib.sh"
load_env_file "${ENV_FILE:-.env}"

ensure_uv
ensure_pnpm_latest

export BACKEND_HOST="${BACKEND_HOST:-0.0.0.0}"
export BACKEND_PORT="${BACKEND_PORT:-8000}"
export FRONTEND_HOST="${FRONTEND_HOST:-0.0.0.0}"
export FRONTEND_PORT="${FRONTEND_PORT:-5173}"
export FRONTEND_DIST_DIR="${FRONTEND_DIST_DIR:-frontend/dist}"
export VITE_API_BASE="${VITE_API_BASE:-}"

uv sync
pnpm -C frontend install
uv run python scripts/init_db.py
pnpm -C frontend build

mkdir -p .run logs

echo "starting backend production:  http://$BACKEND_HOST:$BACKEND_PORT"
echo "starting frontend static:     http://$FRONTEND_HOST:$FRONTEND_PORT"
echo "press Ctrl+C to stop"

./scripts/backend_prod.sh > logs/backend-prod.log 2>&1 &
BACKEND_PID=$!
uv run python scripts/static_frontend.py --host "$FRONTEND_HOST" --port "$FRONTEND_PORT" --directory "$FRONTEND_DIST_DIR" > logs/frontend-prod.log 2>&1 &
FRONTEND_PID=$!

cleanup() {
  echo "stopping production services..."
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
  wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup INT TERM EXIT

sleep 2

if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
  echo "backend production failed to start"
  tail -n 80 logs/backend-prod.log || true
  exit 1
fi

if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
  echo "frontend static failed to start"
  tail -n 80 logs/frontend-prod.log || true
  exit 1
fi

echo "logs:"
echo "  backend:  logs/backend-prod.log"
echo "  frontend: logs/frontend-prod.log"

wait "$BACKEND_PID" "$FRONTEND_PID"
