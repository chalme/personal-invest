from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.database import get_db


def rows_to_dicts(rows: list[Any]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


@dataclass
class SQLiteRepository:
    def fetch_one(self, sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
        with get_db() as conn:
            row = conn.execute(sql, params).fetchone()
            return dict(row) if row else None

    def fetch_all(self, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        with get_db() as conn:
            rows = conn.execute(sql, params).fetchall()
            return rows_to_dicts(rows)

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> int:
        with get_db() as conn:
            cursor = conn.execute(sql, params)
            return int(cursor.lastrowid or 0)

    def execute_many(self, sql: str, values: list[tuple[Any, ...]]) -> None:
        with get_db() as conn:
            conn.executemany(sql, values)

