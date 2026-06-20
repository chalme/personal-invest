#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

source "$ROOT_DIR/scripts/lib.sh"

ensure_uv
ensure_pnpm_latest

uv run python -m compileall backend scripts worker
pnpm -C frontend build
