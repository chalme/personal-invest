from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "storage" / "invest.db"
MIGRATIONS_DIR = ROOT / "backend" / "migrations"
BASELINE_MIGRATION = "001_init"


def migration_files() -> list[Path]:
    return sorted(MIGRATIONS_DIR.glob("*.sql"))


def migration_version(path: Path) -> str:
    return path.stem


def migration_name(path: Path) -> str:
    parts = path.stem.split("_", 1)
    return parts[1] if len(parts) > 1 else path.stem


def ensure_migration_table(conn: sqlite3.Connection) -> None:
    table_path = MIGRATIONS_DIR / "002_schema_migration.sql"
    conn.executescript(table_path.read_text(encoding="utf-8"))


def applied_versions(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute("SELECT version FROM schema_migration").fetchall()
    return {str(row[0]) for row in rows}


def mark_applied(conn: sqlite3.Connection, path: Path) -> None:
    conn.execute(
        """
        INSERT OR IGNORE INTO schema_migration(version, name, applied_at)
        VALUES (?, ?, ?)
        """,
        (
            migration_version(path),
            migration_name(path),
            datetime.now().isoformat(timespec="seconds"),
        ),
    )


def run_migrations(db_path: Path = DB_PATH) -> list[str]:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    applied_now: list[str] = []
    with sqlite3.connect(db_path) as conn:
        ensure_migration_table(conn)
        seen = applied_versions(conn)
        for path in migration_files():
            version = migration_version(path)
            if version == BASELINE_MIGRATION:
                # 001_init.sql is executed by init_db.py and may predate the migration runner.
                mark_applied(conn, path)
                continue
            if version in seen:
                continue
            conn.executescript(path.read_text(encoding="utf-8"))
            mark_applied(conn, path)
            applied_now.append(version)
        conn.commit()
    return applied_now


def main() -> None:
    applied_now = run_migrations()
    if applied_now:
        print("applied migrations: " + ", ".join(applied_now))
    else:
        print("no pending migrations")


if __name__ == "__main__":
    main()
