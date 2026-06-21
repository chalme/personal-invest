#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from audit_real_only import (
    DEFAULT_DB,
    DEFAULT_PARQUET,
    DEFAULT_RAW,
    NON_REAL_MODES,
    NON_REAL_SOURCES,
    PARQUET_TARGETS,
    audit,
    list_sqlite_source_tables,
    quote_identifier,
    source_mask,
    sqlite_where,
    table_columns,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BACKUP_ROOT = ROOT / "backups" / "real-only-purge"


def _stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def _backup_path(root: Path) -> Path:
    path = root / _stamp()
    path.mkdir(parents=True, exist_ok=False)
    return path


def purge_sqlite(db_path: Path, backup_dir: Path, apply: bool) -> dict[str, int]:
    deleted: dict[str, int] = {}
    if not db_path.exists():
        return deleted
    if apply:
        backup_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(db_path, backup_dir / db_path.name)
        for suffix in ("-wal", "-shm"):
            sidecar = Path(f"{db_path}{suffix}")
            if sidecar.exists():
                shutil.copy2(sidecar, backup_dir / sidecar.name)
    with sqlite3.connect(db_path) as conn:
        try:
            conn.execute("BEGIN")
            for table in list_sqlite_source_tables(conn):
                columns = table_columns(conn, table)
                where, params = sqlite_where(columns)
                table_sql = quote_identifier(table)
                count_row = conn.execute(
                    f"SELECT COUNT(*) FROM {table_sql} WHERE {where}", params
                ).fetchone()
                count = int(count_row[0] or 0) if count_row else 0
                if count <= 0:
                    continue
                deleted[table] = count
                if apply:
                    conn.execute(f"DELETE FROM {table_sql} WHERE {where}", params)
            if apply:
                conn.commit()
            else:
                conn.rollback()
        except Exception:
            conn.rollback()
            raise
    return deleted


def _write_partitioned(frame: pd.DataFrame, target: Path, partition_cols: list[str]) -> None:
    tmp = target.with_name(f".{target.name}.real-only-tmp-{_stamp()}")
    if tmp.exists():
        shutil.rmtree(tmp)
    frame.to_parquet(tmp, index=False, partition_cols=partition_cols)
    if target.exists():
        shutil.rmtree(target)
    tmp.rename(target)


def purge_parquet(parquet_dir: Path, backup_dir: Path, apply: bool) -> dict[str, int]:
    removed: dict[str, int] = {}
    partition_cols = {"daily_bar": ["trade_date"], "fund_nav": ["nav_date"]}
    for dataset, source_col in PARQUET_TARGETS.items():
        path = parquet_dir / dataset
        if not path.exists():
            continue
        try:
            frame = pd.read_parquet(path)
        except Exception:
            continue
        if frame.empty or source_col not in frame.columns:
            continue
        mask = source_mask(frame[source_col])
        count = int(mask.sum())
        if count <= 0:
            continue
        removed[dataset] = count
        if not apply:
            continue
        backup_target = backup_dir / "parquet" / dataset
        backup_target.parent.mkdir(parents=True, exist_ok=True)
        if backup_target.exists():
            shutil.rmtree(backup_target)
        shutil.copytree(path, backup_target)
        clean = frame[~mask].copy()
        if clean.empty:
            shutil.rmtree(path)
            continue
        _write_partitioned(clean, path, partition_cols[dataset])
    return removed


def _manifest_is_polluted(data: dict[str, Any]) -> bool:
    source_count = dict(data.get("source_count") or {})
    has_non_real_source = any(
        str(key).lower() in NON_REAL_SOURCES and int(value or 0) > 0
        for key, value in source_count.items()
    )
    mode = str(data.get("source_mode") or "").upper()
    return has_non_real_source or mode in NON_REAL_MODES


def quarantine_manifests(raw_dir: Path, backup_dir: Path, apply: bool) -> dict[str, int]:
    moved: dict[str, int] = {}
    if not raw_dir.exists():
        return moved
    for path in sorted(raw_dir.glob("**/*_manifest.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            data = {"source_mode": "INVALID"}
        if not _manifest_is_polluted(data):
            continue
        dataset = path.parent.name
        moved[dataset] = moved.get(dataset, 0) + 1
        if not apply:
            continue
        target = backup_dir / "raw-manifest" / dataset / path.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), str(target))
    return moved


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Purge runtime non-real data pollution. Dry-run by default."
    )
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--parquet-dir", type=Path, default=DEFAULT_PARQUET)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW)
    parser.add_argument("--backup-root", type=Path, default=DEFAULT_BACKUP_ROOT)
    parser.add_argument(
        "--apply", action="store_true", help="actually delete/rewrite after creating backup"
    )
    args = parser.parse_args()

    backup_dir = _backup_path(args.backup_root) if args.apply else args.backup_root / "dry-run"
    sqlite_deleted = purge_sqlite(args.db, backup_dir, args.apply)
    parquet_removed = purge_parquet(args.parquet_dir, backup_dir, args.apply)
    manifest_moved = quarantine_manifests(args.raw_dir, backup_dir, args.apply)
    after = audit(args.db, args.parquet_dir, args.raw_dir) if args.apply else before

    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"Real-only purge {mode}")
    print(f"Non-real modes: {sorted(NON_REAL_MODES)}; sources: {sorted(NON_REAL_SOURCES)}")
    print(f"Backup dir: {backup_dir if args.apply else 'not created in dry-run'}")
    print(f"SQLite rows to delete: {sqlite_deleted}")
    print(f"Parquet rows to remove: {parquet_removed}")
    print(f"Manifest files to quarantine: {manifest_moved}")
    if args.apply:
        print(f"Remaining polluted rows: {after['summary']}")
    else:
        print("No data changed. Re-run with --apply to purge after reviewing the counts above.")


if __name__ == "__main__":
    main()
