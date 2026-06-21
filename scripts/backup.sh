#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_ROOT="${BACKUP_ROOT:-$ROOT_DIR/backups}"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
TARGET_DIR="$BACKUP_ROOT/$TIMESTAMP"

mkdir -p "$TARGET_DIR"

copy_path() {
  local src="$1"
  local dest="$2"
  if [[ -e "$src" ]]; then
    mkdir -p "$(dirname "$dest")"
    if [[ -d "$src" ]]; then
      if command -v rsync >/dev/null 2>&1; then
        rsync -a "$src/" "$dest/"
      else
        mkdir -p "$dest"
        cp -a "$src/." "$dest/"
      fi
    else
      cp -a "$src" "$dest"
    fi
    echo "OK  $src" >> "$TARGET_DIR/MANIFEST.txt"
  else
    echo "SKIP $src" >> "$TARGET_DIR/MANIFEST.txt"
  fi
}

{
  echo "Personal Invest Backup"
  echo "created_at=$(date -Is)"
  echo "root_dir=$ROOT_DIR"
  echo "backup_dir=$TARGET_DIR"
  echo
} > "$TARGET_DIR/MANIFEST.txt"

copy_path "$ROOT_DIR/storage/invest.db" "$TARGET_DIR/storage/invest.db"
copy_path "$ROOT_DIR/data/parquet" "$TARGET_DIR/data/parquet"
copy_path "$ROOT_DIR/reports" "$TARGET_DIR/reports"
copy_path "$ROOT_DIR/config.yaml" "$TARGET_DIR/config.yaml"
copy_path "$ROOT_DIR/.env.server.example" "$TARGET_DIR/env/.env.server.example"

cat >> "$TARGET_DIR/MANIFEST.txt" <<'NOTE'

Note:
- .env.server is intentionally not backed up by default because it may contain secrets.
- Set BACKUP_ROOT=/path/to/backups to write backups outside the repository.
- First version is local-only and unencrypted; choose external storage/encryption manually if needed.
NOTE

echo "Backup created: $TARGET_DIR"
