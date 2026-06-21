#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

source "$ROOT_DIR/scripts/lib.sh"
load_env_file "${ENV_FILE:-.env}"

ensure_python_runtime


export FRONTEND_HOST="${FRONTEND_HOST:-0.0.0.0}"
export FRONTEND_PORT="${FRONTEND_PORT:-5173}"
export FRONTEND_DIST_DIR="${FRONTEND_DIST_DIR:-frontend/dist}"
export VITE_API_BASE="${VITE_API_BASE:-}"

if [ "${FRONTEND_BUILD_ON_START:-1}" = "1" ]; then
  ensure_pnpm_latest
  pnpm -C frontend install
  pnpm -C frontend build
  run_python scripts/write_runtime_config.py --output "$FRONTEND_DIST_DIR/config.js"
elif [ ! -f "$FRONTEND_DIST_DIR/index.html" ]; then
  echo "缺少前端构建产物：$FRONTEND_DIST_DIR/index.html"
  echo "请先执行：pnpm -C frontend install && pnpm -C frontend build"
  exit 1
fi

run_python scripts/static_frontend.py --host "$FRONTEND_HOST" --port "$FRONTEND_PORT" --directory "$FRONTEND_DIST_DIR"
