#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

source "$ROOT_DIR/scripts/lib.sh"

ensure_uv
ensure_pnpm_latest

export BACKEND_HOST="${BACKEND_HOST:-0.0.0.0}"
export BACKEND_PORT="${BACKEND_PORT:-8000}"
export FRONTEND_HOST="${FRONTEND_HOST:-0.0.0.0}"
export FRONTEND_PORT="${FRONTEND_PORT:-5173}"
export VITE_API_BASE="${VITE_API_BASE:-}"

uv sync
pnpm -C frontend install
uv run python scripts/init_db.py

mkdir -p .run logs

echo "starting backend:  http://$BACKEND_HOST:$BACKEND_PORT"
echo "starting frontend: http://$FRONTEND_HOST:$FRONTEND_PORT"
echo "local access:"
echo "  frontend: http://localhost:$FRONTEND_PORT"
echo "  backend:  http://localhost:$BACKEND_PORT"
echo "remote access:"
echo "  frontend: http://<server-ip>:$FRONTEND_PORT"
echo "  backend:  http://<server-ip>:$BACKEND_PORT"
echo "press Ctrl+C to stop"

./scripts/backend.sh > logs/backend.log 2>&1 &
BACKEND_PID=$!
./scripts/frontend.sh > logs/frontend.log 2>&1 &
FRONTEND_PID=$!

cleanup() {
  echo "stopping services..."
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
  wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup INT TERM EXIT

sleep 2

if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
  echo "backend failed to start"
  tail -n 80 logs/backend.log || true
  exit 1
fi

if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
  echo "frontend failed to start"
  tail -n 80 logs/frontend.log || true
  exit 1
fi

echo "logs:"
echo "  backend:  logs/backend.log"
echo "  frontend: logs/frontend.log"

wait "$BACKEND_PID" "$FRONTEND_PID"
