#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "storage" / "invest.db"
DEFAULT_PARQUET = ROOT / "data" / "parquet"
DEFAULT_RAW = ROOT / "data" / "raw"

NON_REAL_SOURCES = {
    "sample",
    "estimated",
    "built_in_sample",
    "deterministic_estimate",
    "instrument_estimate",
    "mock",
    "demo",
}
NON_REAL_MODES = {"SAMPLE", "ESTIMATED"}
REAL_CACHE_SOURCES = {"akshare_cached", "real_cached", "historical_parquet"}

PARQUET_TARGETS = {
    "daily_bar": "source",
    "fund_nav": "source",
}


@dataclass(frozen=True)
class SqliteFinding:
    table: str
    count: int
    source_count: dict[str, int]
    source_mode_count: dict[str, int]


@dataclass(frozen=True)
class ParquetFinding:
    dataset: str
    count: int
    source_count: dict[str, int]
    path: str


@dataclass(frozen=True)
class ManifestFinding:
    dataset: str
    path: str
    source_mode: str | None
    source_count: dict[str, int]
    polluted_count: int
    reason: str


def quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({quote_identifier(table)})").fetchall()
    return {str(row[1]) for row in rows}


def list_sqlite_source_tables(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    tables: list[str] = []
    for row in rows:
        table = str(row[0])
        columns = table_columns(conn, table)
        if {"source", "source_mode"} & columns:
            tables.append(table)
    return sorted(tables)


def sqlite_where(columns: set[str]) -> tuple[str, list[Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if "source_mode" in columns:
        clauses.append(
            "UPPER(COALESCE(source_mode, '')) IN ({})".format(
                ",".join("?" for _ in NON_REAL_MODES)
            )
        )
        params.extend(sorted(NON_REAL_MODES))
    if "source" in columns:
        clauses.append(
            "LOWER(COALESCE(source, '')) IN ({})".format(
                ",".join("?" for _ in NON_REAL_SOURCES)
            )
        )
        params.extend(sorted(NON_REAL_SOURCES))
    if not clauses:
        return "0", []
    return " OR ".join(f"({clause})" for clause in clauses), params


def audit_sqlite(db_path: Path = DEFAULT_DB) -> list[SqliteFinding]:
    if not db_path.exists():
        return []
    findings: list[SqliteFinding] = []
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        for table in list_sqlite_source_tables(conn):
            columns = table_columns(conn, table)
            where, params = sqlite_where(columns)
            table_sql = quote_identifier(table)
            row = conn.execute(
                f"SELECT COUNT(*) AS count FROM {table_sql} WHERE {where}", params
            ).fetchone()
            count = int(row["count"] or 0) if row else 0
            if count <= 0:
                continue
            source_count: dict[str, int] = {}
            source_mode_count: dict[str, int] = {}
            if "source" in columns:
                source_sql = (
                    "SELECT COALESCE(source, 'NULL') AS key, COUNT(*) AS count "
                    f"FROM {table_sql} WHERE {where} "
                    "GROUP BY COALESCE(source, 'NULL')"
                )
                for source_row in conn.execute(source_sql, params):
                    source_count[str(source_row["key"])] = int(source_row["count"] or 0)
            if "source_mode" in columns:
                mode_sql = (
                    "SELECT UPPER(COALESCE(source_mode, 'NULL')) AS key, "
                    f"COUNT(*) AS count FROM {table_sql} WHERE {where} "
                    "GROUP BY UPPER(COALESCE(source_mode, 'NULL'))"
                )
                for mode_row in conn.execute(mode_sql, params):
                    source_mode_count[str(mode_row["key"])] = int(mode_row["count"] or 0)
            findings.append(SqliteFinding(table, count, source_count, source_mode_count))
    return findings


def source_mask(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.lower().isin(NON_REAL_SOURCES)


def audit_parquet(parquet_dir: Path = DEFAULT_PARQUET) -> list[ParquetFinding]:
    findings: list[ParquetFinding] = []
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
        bad = frame[source_mask(frame[source_col])]
        if bad.empty:
            continue
        counts = bad[source_col].fillna("NULL").astype(str).value_counts().to_dict()
        findings.append(
            ParquetFinding(
                dataset=dataset,
                count=int(len(bad)),
                source_count={str(k): int(v) for k, v in counts.items()},
                path=str(path),
            )
        )
    return findings


def _count_non_real_sources(source_count: dict[str, Any]) -> int:
    total = 0
    for key, value in source_count.items():
        if str(key).lower() in NON_REAL_SOURCES:
            total += int(value or 0)
    return total


def _manifest_reason(source_mode: str | None, source_count: dict[str, Any]) -> tuple[int, str | None]:
    polluted_count = _count_non_real_sources(source_count)
    mode = str(source_mode or "").upper()
    if mode in NON_REAL_MODES:
        return max(polluted_count, 1), f"source_mode={mode}"
    if polluted_count > 0:
        return polluted_count, "source_count contains non-real sources"
    if mode == "MIXED" and polluted_count > 0:
        return polluted_count, "MIXED contains non-real sources"
    return 0, None


def audit_manifest(raw_dir: Path = DEFAULT_RAW) -> list[ManifestFinding]:
    findings: list[ManifestFinding] = []
    if not raw_dir.exists():
        return findings
    for path in sorted(raw_dir.glob("**/*_manifest.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            findings.append(
                ManifestFinding(
                    dataset=path.parent.name,
                    path=str(path),
                    source_mode=None,
                    source_count={},
                    polluted_count=1,
                    reason=f"invalid manifest json: {exc.__class__.__name__}",
                )
            )
            continue
        source_count = dict(data.get("source_count") or {})
        source_mode = data.get("source_mode")
        polluted_count, reason = _manifest_reason(source_mode, source_count)
        if reason:
            findings.append(
                ManifestFinding(
                    dataset=path.parent.name,
                    path=str(path),
                    source_mode=str(source_mode) if source_mode is not None else None,
                    source_count={str(k): int(v or 0) for k, v in source_count.items()},
                    polluted_count=polluted_count,
                    reason=reason,
                )
            )
    return findings


def audit(
    db_path: Path = DEFAULT_DB,
    parquet_dir: Path = DEFAULT_PARQUET,
    raw_dir: Path = DEFAULT_RAW,
) -> dict[str, Any]:
    sqlite_findings = audit_sqlite(db_path)
    parquet_findings = audit_parquet(parquet_dir)
    manifest_findings = audit_manifest(raw_dir)
    return {
        "sqlite": [finding.__dict__ for finding in sqlite_findings],
        "parquet": [finding.__dict__ for finding in parquet_findings],
        "manifest": [finding.__dict__ for finding in manifest_findings],
        "summary": {
            "sqlite_polluted_rows": sum(item.count for item in sqlite_findings),
            "parquet_polluted_rows": sum(item.count for item in parquet_findings),
            "manifest_polluted_files": len(manifest_findings),
            "manifest_polluted_records": sum(item.polluted_count for item in manifest_findings),
            "sqlite_table_count": len(sqlite_findings),
            "parquet_dataset_count": len(parquet_findings),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit runtime non-real data pollution.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--parquet-dir", type=Path, default=DEFAULT_PARQUET)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW)
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    args = parser.parse_args()
    result = audit(args.db, args.parquet_dir, args.raw_dir)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    print("Real-only audit")
    print(f"SQLite polluted rows: {result['summary']['sqlite_polluted_rows']}")
    for item in result["sqlite"]:
        print(
            f"- sqlite:{item['table']} rows={item['count']} "
            f"modes={item['source_mode_count']} sources={item['source_count']}"
        )
    print(f"Parquet polluted rows: {result['summary']['parquet_polluted_rows']}")
    for item in result["parquet"]:
        print(
            f"- parquet:{item['dataset']} rows={item['count']} "
            f"sources={item['source_count']} path={item['path']}"
        )
    print(f"Manifest polluted files: {result['summary']['manifest_polluted_files']}")
    for item in result["manifest"]:
        print(
            f"- manifest:{item['path']} polluted={item['polluted_count']} "
            f"mode={item['source_mode']} sources={item['source_count']} reason={item['reason']}"
        )


if __name__ == "__main__":
    main()
