#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

source "$ROOT_DIR/scripts/lib.sh"
load_env_file "${ENV_FILE:-.env}"

ensure_uv
ensure_pnpm_latest

export FRONTEND_HOST="${FRONTEND_HOST:-0.0.0.0}"
export FRONTEND_PORT="${FRONTEND_PORT:-5173}"
export FRONTEND_DIST_DIR="${FRONTEND_DIST_DIR:-frontend/dist}"
export VITE_API_BASE="${VITE_API_BASE:-}"

pnpm -C frontend install
pnpm -C frontend build
uv run python scripts/static_frontend.py --host "$FRONTEND_HOST" --port "$FRONTEND_PORT" --directory "$FRONTEND_DIST_DIR"
