from __future__ import annotations

import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "storage" / "invest.db"
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PARQUET_DIR = DATA_DIR / "parquet"
TMP_DIR = DATA_DIR / "tmp"
REPORT_DIR = ROOT / "reports"


def connect_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def get_watchlist(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT
            w.symbol,
            COALESCE(i.name, w.name) AS name,
            COALESCE(i.asset_type, w.asset_type) AS asset_type,
            COALESCE(i.market, w.market) AS market,
            w.group_name,
            i.sector_code,
            COALESCE(i.sector_name, w.group_name) AS sector_name,
            i.fund_type,
            i.risk_level,
            w.priority
        FROM watchlist w
        LEFT JOIN instrument i ON i.symbol = w.symbol
        WHERE w.status = 'ACTIVE'
        ORDER BY w.priority DESC, w.symbol ASC
        """
    ).fetchall()
    return rows_to_dicts(rows)


def write_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def replace_dir_atomic(target: Path, src: Path) -> None:
    backup = target.with_name(target.name + ".bak")
    if backup.exists():
        shutil.rmtree(backup)
    if target.exists():
        target.rename(backup)
    src.rename(target)
    if backup.exists():
        shutil.rmtree(backup)


def write_partitioned_parquet(df: pd.DataFrame, dataset_name: str, partition_cols: list[str]) -> Path:
    if df.empty:
        raise ValueError(f"{dataset_name} dataframe is empty")
    target = PARQUET_DIR / dataset_name
    tmp = TMP_DIR / f"{dataset_name}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(tmp, index=False, partition_cols=partition_cols)
    replace_dir_atomic(target, tmp)
    return target


def read_parquet_dataset(dataset_name: str) -> pd.DataFrame:
    target = PARQUET_DIR / dataset_name
    if not target.exists():
        return pd.DataFrame()
    return pd.read_parquet(target)


def upsert_many(conn: sqlite3.Connection, sql: str, values: list[tuple[Any, ...]]) -> int:
    if not values:
        return 0
    conn.executemany(sql, values)
    conn.commit()
    return len(values)
