#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

source "$ROOT_DIR/scripts/lib.sh"
load_env_file "${ENV_FILE:-.env}"

ensure_uv
ensure_pnpm_latest

uv sync
pnpm -C frontend install
uv run python scripts/init_db.py

echo "setup completed"
echo "backend:  http://localhost:${BACKEND_PORT:-8000}"
echo "frontend: http://localhost:${FRONTEND_PORT:-5173}"
