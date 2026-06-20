#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

source "$ROOT_DIR/scripts/lib.sh"
load_env_file "${ENV_FILE:-.env}"

ensure_uv

export PYTHONPATH="$ROOT_DIR/backend${PYTHONPATH:+:$PYTHONPATH}"
export BACKEND_HOST="${BACKEND_HOST:-0.0.0.0}"
export BACKEND_PORT="${BACKEND_PORT:-8000}"
export UVICORN_WORKERS="${UVICORN_WORKERS:-1}"

uv run uvicorn app.main:app \
  --app-dir backend \
  --host "$BACKEND_HOST" \
  --port "$BACKEND_PORT" \
  --workers "$UVICORN_WORKERS"
