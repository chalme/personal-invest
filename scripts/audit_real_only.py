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

SQLITE_TARGETS = (
    "financial_statement_snapshot",
    "financial_metric_snapshot",
    "valuation_snapshot",
    "stock_quality_snapshot",
    "fund_profile",
    "fund_manager_profile",
    "fund_company_profile",
    "fund_risk_return_snapshot",
    "fund_benchmark_snapshot",
    "fund_peer_rank_snapshot",
    "fund_holding_exposure_snapshot",
    "etf_profile",
    "etf_exposure_snapshot",
    "etf_liquidity_snapshot",
    "etf_risk_return_snapshot",
    "etf_tracking_snapshot",
)

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


def _table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {str(row[1]) for row in rows}


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone()
    return bool(row)


def _sqlite_where(columns: set[str]) -> tuple[str, list[Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if "source_mode" in columns:
        clauses.append(
            "UPPER(COALESCE(source_mode, '')) IN ({})".format(",".join("?" for _ in NON_REAL_MODES))
        )
        params.extend(sorted(NON_REAL_MODES))
    if "source" in columns:
        clauses.append(
            "LOWER(COALESCE(source, '')) IN ({})".format(",".join("?" for _ in NON_REAL_SOURCES))
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
        for table in SQLITE_TARGETS:
            if not _table_exists(conn, table):
                continue
            columns = _table_columns(conn, table)
            where, params = _sqlite_where(columns)
            row = conn.execute(
                f"SELECT COUNT(*) AS count FROM {table} WHERE {where}", params
            ).fetchone()
            count = int(row["count"] or 0) if row else 0
            if count <= 0:
                continue
            source_count: dict[str, int] = {}
            source_mode_count: dict[str, int] = {}
            if "source" in columns:
                source_sql = (
                    f"SELECT COALESCE(source, 'NULL') AS key, COUNT(*) AS count "
                    f"FROM {table} WHERE {where} "
                    "GROUP BY COALESCE(source, 'NULL')"
                )
                for source_row in conn.execute(
                    source_sql,
                    params,
                ):
                    source_count[str(source_row["key"])] = int(source_row["count"] or 0)
            if "source_mode" in columns:
                mode_sql = (
                    f"SELECT UPPER(COALESCE(source_mode, 'NULL')) AS key, "
                    f"COUNT(*) AS count FROM {table} WHERE {where} "
                    "GROUP BY UPPER(COALESCE(source_mode, 'NULL'))"
                )
                for mode_row in conn.execute(
                    mode_sql,
                    params,
                ):
                    source_mode_count[str(mode_row["key"])] = int(mode_row["count"] or 0)
            findings.append(SqliteFinding(table, count, source_count, source_mode_count))
    return findings


def _source_mask(series: pd.Series) -> pd.Series:
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
        bad = frame[_source_mask(frame[source_col])]
        if bad.empty:
            continue
        counts = bad[source_col].fillna("NULL").astype(str).value_counts().to_dict()
        findings.append(
            ParquetFinding(
                dataset, int(len(bad)), {str(k): int(v) for k, v in counts.items()}, str(path)
            )
        )
    return findings


def audit(db_path: Path = DEFAULT_DB, parquet_dir: Path = DEFAULT_PARQUET) -> dict[str, Any]:
    sqlite_findings = audit_sqlite(db_path)
    parquet_findings = audit_parquet(parquet_dir)
    return {
        "sqlite": [finding.__dict__ for finding in sqlite_findings],
        "parquet": [finding.__dict__ for finding in parquet_findings],
        "summary": {
            "sqlite_polluted_rows": sum(item.count for item in sqlite_findings),
            "parquet_polluted_rows": sum(item.count for item in parquet_findings),
            "sqlite_table_count": len(sqlite_findings),
            "parquet_dataset_count": len(parquet_findings),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit runtime non-real data pollution.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--parquet-dir", type=Path, default=DEFAULT_PARQUET)
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    args = parser.parse_args()
    result = audit(args.db, args.parquet_dir)
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


if __name__ == "__main__":
    main()
