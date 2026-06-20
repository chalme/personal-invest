#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

source "$ROOT_DIR/scripts/lib.sh"
load_env_file "${ENV_FILE:-.env}"

ensure_pnpm_latest

export VITE_API_BASE="${VITE_API_BASE:-}"
export FRONTEND_HOST="${FRONTEND_HOST:-0.0.0.0}"
export FRONTEND_PORT="${FRONTEND_PORT:-5173}"

pnpm -C frontend dev -- --host "$FRONTEND_HOST" --port "$FRONTEND_PORT"
