#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd
from audit_real_only import (
    DEFAULT_DB,
    DEFAULT_PARQUET,
    NON_REAL_MODES,
    NON_REAL_SOURCES,
    PARQUET_TARGETS,
    SQLITE_TARGETS,
    _source_mask,
    _sqlite_where,
    _table_columns,
    _table_exists,
    audit,
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
        shutil.copy2(db_path, backup_dir / db_path.name)
        wal = db_path.with_suffix(db_path.suffix + "-wal")
        shm = db_path.with_suffix(db_path.suffix + "-shm")
        if wal.exists():
            shutil.copy2(wal, backup_dir / wal.name)
        if shm.exists():
            shutil.copy2(shm, backup_dir / shm.name)
    with sqlite3.connect(db_path) as conn:
        for table in SQLITE_TARGETS:
            if not _table_exists(conn, table):
                continue
            columns = _table_columns(conn, table)
            where, params = _sqlite_where(columns)
            count_row = conn.execute(
                f"SELECT COUNT(*) FROM {table} WHERE {where}", params
            ).fetchone()
            count = int(count_row[0] or 0) if count_row else 0
            if count <= 0:
                continue
            deleted[table] = count
            if apply:
                conn.execute(f"DELETE FROM {table} WHERE {where}", params)
        if apply:
            conn.commit()
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
        mask = _source_mask(frame[source_col])
        count = int(mask.sum())
        if count <= 0:
            continue
        removed[dataset] = count
        if not apply:
            continue
        backup_target = backup_dir / "parquet" / dataset
        backup_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(path, backup_target)
        clean = frame[~mask].copy()
        if clean.empty:
            shutil.rmtree(path)
            continue
        _write_partitioned(clean, path, partition_cols[dataset])
    return removed


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Purge runtime non-real data pollution. Dry-run by default."
    )
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--parquet-dir", type=Path, default=DEFAULT_PARQUET)
    parser.add_argument("--backup-root", type=Path, default=DEFAULT_BACKUP_ROOT)
    parser.add_argument(
        "--apply", action="store_true", help="actually delete/rewrite after creating backup"
    )
    args = parser.parse_args()

    before = audit(args.db, args.parquet_dir)
    backup_dir = _backup_path(args.backup_root) if args.apply else args.backup_root / "dry-run"
    sqlite_deleted = purge_sqlite(args.db, backup_dir, args.apply)
    parquet_removed = purge_parquet(args.parquet_dir, backup_dir, args.apply)
    after = audit(args.db, args.parquet_dir) if args.apply else before

    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"Real-only purge {mode}")
    print(f"Non-real modes: {sorted(NON_REAL_MODES)}; sources: {sorted(NON_REAL_SOURCES)}")
    print(f"Backup dir: {backup_dir if args.apply else 'not created in dry-run'}")
    print(f"SQLite rows to delete: {sqlite_deleted}")
    print(f"Parquet rows to remove: {parquet_removed}")
    if args.apply:
        print(f"Remaining polluted rows: {after['summary']}")
    else:
        print("No data changed. Re-run with --apply to purge after reviewing the counts above.")


if __name__ == "__main__":
    main()
