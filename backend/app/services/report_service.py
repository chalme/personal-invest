from __future__ import annotations

from pathlib import Path
from typing import Any

import markdown

from app.core.config import get_settings
from app.repositories.sqlite_repo import SQLiteRepository


class ReportService:
    def __init__(self, repo: SQLiteRepository | None = None) -> None:
        self.repo = repo or SQLiteRepository()
        self.settings = get_settings()

    def daily_reports(self, limit: int = 30) -> list[dict[str, Any]]:
        limit = max(1, min(limit, 100))
        return self.repo.fetch_all(
            """
            SELECT * FROM report_index
            WHERE report_type = 'daily'
            ORDER BY report_date DESC, id DESC
            LIMIT ?
            """,
            (limit,),
        )

    def latest_daily_report(self) -> dict[str, Any] | None:
        row = self.repo.fetch_one(
            """
            SELECT * FROM report_index
            WHERE report_type = 'daily'
            ORDER BY report_date DESC, id DESC
            LIMIT 1
            """
        )
        if not row:
            return None
        return self._with_content(row)

    def daily_report_by_date(self, report_date: str) -> dict[str, Any] | None:
        row = self.repo.fetch_one(
            """
            SELECT * FROM report_index
            WHERE report_type = 'daily' AND report_date = ?
            LIMIT 1
            """,
            (report_date,),
        )
        if not row:
            return None
        return self._with_content(row)

    def _with_content(self, row: dict[str, Any]) -> dict[str, Any]:
        markdown_text = ""
        path_value = row.get("markdown_path")
        if path_value:
            path = self._resolve_report_path(str(path_value))
            if path.exists() and path.is_file():
                markdown_text = path.read_text(encoding="utf-8")
        row["markdown"] = markdown_text
        row["html"] = markdown.markdown(markdown_text, extensions=["tables", "fenced_code"]) if markdown_text else ""
        return row

    def _resolve_report_path(self, path_value: str) -> Path:
        candidate = Path(path_value)
        if candidate.is_absolute():
            return candidate
        return self.settings.root_dir / candidate
