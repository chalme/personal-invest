from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime
from typing import Any

from app.repositories.sqlite_repo import SQLiteRepository


DEFAULT_STRATEGY_CONFIG: dict[str, Any] = {
    "strategy_code": "personal_watch_v1",
    "strategy_name": "个人观察策略 V1",
    "enabled": True,
    "params": {
        "high_quality_score": 80,
        "high_quality_market_score": 45,
        "trend_watch_score": 65,
        "trend_watch_market_score": 55,
        "risk_score": 45,
    },
}


class StrategyConfigService:
    def __init__(self) -> None:
        self.repo = SQLiteRepository()

    def list_configs(self) -> list[dict[str, Any]]:
        rows = self.repo.fetch_all(
            """
            SELECT strategy_code, strategy_name, enabled, config_json, updated_at
            FROM strategy_config
            ORDER BY strategy_code
            """
        )
        if not rows:
            config = self.ensure_default_config()
            return [config]
        return [self._parse_row(row) for row in rows]

    def get_config(self, strategy_code: str) -> dict[str, Any]:
        row = self.repo.fetch_one(
            """
            SELECT strategy_code, strategy_name, enabled, config_json, updated_at
            FROM strategy_config
            WHERE strategy_code = ?
            """,
            (strategy_code,),
        )
        if row:
            return self._parse_row(row)
        if strategy_code == DEFAULT_STRATEGY_CONFIG["strategy_code"]:
            return self.ensure_default_config()
        raise KeyError(f"strategy not found: {strategy_code}")

    def upsert_config(self, payload: dict[str, Any]) -> dict[str, Any]:
        strategy_code = str(payload.get("strategy_code") or DEFAULT_STRATEGY_CONFIG["strategy_code"])
        existing = self.get_config(strategy_code) if self._exists(strategy_code) else deepcopy(DEFAULT_STRATEGY_CONFIG)
        strategy_name = str(payload.get("strategy_name") or existing.get("strategy_name") or strategy_code)
        enabled = bool(payload.get("enabled", existing.get("enabled", True)))
        params = dict(existing.get("params") or {})
        params.update(payload.get("params") or {})
        normalized = self._normalize_params(params)
        now = datetime.now().isoformat(timespec="seconds")
        self.repo.execute(
            """
            INSERT INTO strategy_config(strategy_code, strategy_name, enabled, config_json, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(strategy_code) DO UPDATE SET
                strategy_name = excluded.strategy_name,
                enabled = excluded.enabled,
                config_json = excluded.config_json,
                updated_at = excluded.updated_at
            """,
            (strategy_code, strategy_name, 1 if enabled else 0, json.dumps(normalized, ensure_ascii=False), now),
        )
        return self.get_config(strategy_code)

    def reset_default_config(self) -> dict[str, Any]:
        config = deepcopy(DEFAULT_STRATEGY_CONFIG)
        return self.upsert_config(config)

    def ensure_default_config(self) -> dict[str, Any]:
        if self._exists(DEFAULT_STRATEGY_CONFIG["strategy_code"]):
            return self.get_config(DEFAULT_STRATEGY_CONFIG["strategy_code"])
        return self.upsert_config(DEFAULT_STRATEGY_CONFIG)

    def _exists(self, strategy_code: str) -> bool:
        row = self.repo.fetch_one("SELECT 1 AS ok FROM strategy_config WHERE strategy_code = ?", (strategy_code,))
        return row is not None

    def _parse_row(self, row: dict[str, Any]) -> dict[str, Any]:
        try:
            params = json.loads(row.get("config_json") or "{}")
        except json.JSONDecodeError:
            params = {}
        normalized = self._normalize_params(params)
        return {
            "strategy_code": row["strategy_code"],
            "strategy_name": row["strategy_name"],
            "enabled": bool(row["enabled"]),
            "params": normalized,
            "updated_at": row.get("updated_at"),
        }

    def _normalize_params(self, params: dict[str, Any]) -> dict[str, float]:
        defaults = DEFAULT_STRATEGY_CONFIG["params"]
        normalized: dict[str, float] = {}
        for key, default in defaults.items():
            try:
                value = float(params.get(key, default))
            except (TypeError, ValueError):
                value = float(default)
            if "score" in key:
                value = min(100.0, max(0.0, value))
            normalized[key] = value
        return normalized
