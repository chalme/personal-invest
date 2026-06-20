from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.core.config import get_settings


class DataSourceService:
    def __init__(self, raw_market_dir: Path | None = None) -> None:
        settings = get_settings()
        self.raw_market_dir = raw_market_dir or settings.data_dir / "raw" / "market"

    def latest_market_manifest(self) -> dict[str, Any] | None:
        if not self.raw_market_dir.exists():
            return None
        manifests = sorted(self.raw_market_dir.glob("*_manifest.json"), key=lambda item: item.name, reverse=True)
        for manifest_path in manifests:
            try:
                return json.loads(manifest_path.read_text(encoding="utf-8")) | {"manifest_file": manifest_path.name}
            except Exception:
                continue
        return None

    def market_source_summary(self) -> dict[str, Any]:
        manifest = self.latest_market_manifest()
        if not manifest:
            return {
                "status": "missing",
                "mode": "unknown",
                "latest_trade_date": None,
                "generated_at": None,
                "rows": 0,
                "symbol_count": 0,
                "source_count": {},
                "has_sample_data": False,
                "has_real_data": False,
                "warning": "尚未发现行情数据来源记录，请先执行每日更新。",
            }

        source_count = dict(manifest.get("source_count") or {})
        sample_count = int(source_count.get("sample") or 0)
        real_count = sum(int(value or 0) for key, value in source_count.items() if key != "sample")
        has_sample_data = sample_count > 0
        has_real_data = real_count > 0
        if has_sample_data and has_real_data:
            mode = "mixed"
            warning = "当前行情包含真实数据和样本数据，分析结论需要结合数据来源谨慎使用。"
        elif has_sample_data:
            mode = "sample"
            warning = "当前行情全部来自样本数据，仅用于功能演示，不应作为真实投资依据。"
        elif has_real_data:
            mode = "real"
            warning = None
        else:
            mode = "unknown"
            warning = "行情数据来源不明确，请检查数据同步任务。"

        symbols = manifest.get("symbols") or []
        return {
            "status": "ok",
            "mode": mode,
            "latest_trade_date": manifest.get("latest_trade_date"),
            "generated_at": manifest.get("generated_at"),
            "rows": int(manifest.get("rows") or 0),
            "symbol_count": len(symbols),
            "source_count": source_count,
            "has_sample_data": has_sample_data,
            "has_real_data": has_real_data,
            "warning": warning,
            "manifest_file": manifest.get("manifest_file"),
        }
