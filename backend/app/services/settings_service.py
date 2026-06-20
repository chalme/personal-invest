from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from app.repositories.sqlite_repo import SQLiteRepository


DEFAULT_SETTINGS: dict[str, Any] = {
    "risk": {
        "market_weak_score": 40,
        "single_position_limit": 0.20,
        "stock_weak_score": 50,
        "enable_stop_loss_check": True,
    },
    "data": {
        "source_mode": "auto",
        "prefer_akshare": True,
        "fallback_to_sample": True,
    },
    "ai": {
        "enabled": True,
        "provider": "local",
        "external_llm_enabled": False,
    },
    "ui": {
        "theme": "dark",
        "density": "comfortable",
    },
}


class SettingsService:
    def __init__(self, repo: SQLiteRepository | None = None) -> None:
        self.repo = repo or SQLiteRepository()

    def get_settings(self) -> dict[str, Any]:
        merged = json.loads(json.dumps(DEFAULT_SETTINGS))
        rows = self.repo.fetch_all("SELECT key, value FROM user_setting")
        for row in rows:
            key = str(row["key"])
            value = self._decode(row["value"])
            self._set_nested(merged, key, value)
        return merged

    def update_settings(self, payload: dict[str, Any]) -> dict[str, Any]:
        flattened = self._flatten(payload)
        now = datetime.now().isoformat(timespec="seconds")
        for key, value in flattened.items():
            self.repo.execute(
                """
                INSERT INTO user_setting(key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = excluded.updated_at
                """,
                (key, json.dumps(value, ensure_ascii=False), now),
            )
        return self.get_settings()

    def reset_settings(self) -> dict[str, Any]:
        self.repo.execute("DELETE FROM user_setting")
        return self.get_settings()

    @staticmethod
    def _decode(value: str) -> Any:
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value

    @staticmethod
    def _flatten(payload: dict[str, Any], prefix: str = "") -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in payload.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            if isinstance(value, dict):
                result.update(SettingsService._flatten(value, path))
            else:
                result[path] = value
        return result

    @staticmethod
    def _set_nested(target: dict[str, Any], path: str, value: Any) -> None:
        parts = path.split(".")
        cursor = target
        for part in parts[:-1]:
            current = cursor.get(part)
            if not isinstance(current, dict):
                current = {}
                cursor[part] = current
            cursor = current
        cursor[parts[-1]] = value
