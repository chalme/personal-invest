from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.repositories.sqlite_repo import SQLiteRepository
from app.services.data_source_service import DataSourceService


@dataclass(frozen=True)
class ModuleSpec:
    key: str
    label: str
    tables: tuple[tuple[str, str, str], ...]
    default_missing_note: str
    can_drive_advice_when_real: bool = True


class DataCredibilityService:
    """Aggregate data source credibility across analysis modules."""

    def __init__(self, repo: SQLiteRepository | None = None) -> None:
        self.repo = repo or SQLiteRepository()
        self.settings = get_settings()
        self.data_source = DataSourceService()

    def overview(self) -> dict[str, Any]:
        modules = [
            self._market_module(),
            self._daily_bar_module(),
            self._fund_nav_module(),
            self._table_module(
                ModuleSpec(
                    key="stock_financial",
                    label="股票财报",
                    tables=(
                        ("financial_statement_snapshot", "data_date", "source_mode"),
                        ("financial_metric_snapshot", "data_date", "source_mode"),
                        ("valuation_snapshot", "data_date", "source_mode"),
                        ("stock_quality_snapshot", "data_date", "source_mode"),
                    ),
                    default_missing_note="尚未生成股票财报、估值和公司质量快照。",
                )
            ),
            self._table_module(
                ModuleSpec(
                    key="fund_deep",
                    label="场外基金深度",
                    tables=(
                        ("fund_profile", "data_date", "source_mode"),
                        ("fund_risk_return_snapshot", "data_date", "source_mode"),
                        ("fund_benchmark_snapshot", "data_date", "source_mode"),
                        ("fund_peer_rank_snapshot", "data_date", "source_mode"),
                        ("fund_holding_exposure_snapshot", "data_date", "source_mode"),
                    ),
                    default_missing_note="尚未发现 active FUND 资产或基金深度快照。",
                )
            ),
            self._table_module(
                ModuleSpec(
                    key="etf_deep",
                    label="ETF 深度",
                    tables=(
                        ("etf_profile", "data_date", "source_mode"),
                        ("etf_exposure_snapshot", "data_date", "source_mode"),
                        ("etf_liquidity_snapshot", "data_date", "source_mode"),
                        ("etf_risk_return_snapshot", "data_date", "source_mode"),
                        ("etf_tracking_snapshot", "data_date", "source_mode"),
                    ),
                    default_missing_note="尚未生成 ETF 画像、流动性、风险收益或跟踪质量快照。",
                )
            ),
            self._portfolio_snapshot_module(),
            self._review_loop_module(),
        ]
        return {"summary": self._summary(modules), "modules": modules}

    def _market_module(self) -> dict[str, Any]:
        source = self.data_source.market_source_summary()
        mode = self._normalize_mode(source.get("mode"))
        count = int(source.get("rows") or 0)
        note = source.get("warning") or self._mode_note(mode, "市场行情")
        return self._module(
            module="market_data",
            label="市场行情",
            source_mode=mode,
            latest_data_date=source.get("latest_trade_date"),
            record_count=count,
            coverage_ratio=1.0 if count else 0.0,
            can_drive_advice=mode == "REAL",
            risk_level=self._risk_for_mode(mode),
            note=note,
        )

    def _daily_bar_module(self) -> dict[str, Any]:
        base = self.settings.data_dir / "parquet" / "daily_bar"
        file_count, latest_date = self._partition_stats(base, "trade_date=")
        market_mode = self._normalize_mode(self.data_source.market_source_summary().get("mode"))
        mode = market_mode if file_count else "MISSING"
        return self._module(
            module="daily_bar",
            label="行情日线",
            source_mode=mode,
            latest_data_date=latest_date,
            record_count=file_count,
            coverage_ratio=1.0 if file_count else 0.0,
            can_drive_advice=mode == "REAL",
            risk_level=self._risk_for_mode(mode),
            note=self._mode_note(mode, "行情日线"),
        )

    def _fund_nav_module(self) -> dict[str, Any]:
        base = self.settings.data_dir / "parquet" / "fund_nav"
        file_count, latest_date = self._partition_stats(base, "nav_date=")
        manifest = self._latest_raw_manifest("fund")
        source_count = dict((manifest or {}).get("source_count") or {})
        manifest_rows = int((manifest or {}).get("rows") or 0)
        record_count = manifest_rows if manifest else file_count
        mode = self._mode_from_source_count(source_count)
        if record_count <= 0 and file_count <= 0:
            mode = "MISSING"
        if mode == "MISSING" and file_count > 0 and not manifest:
            mode = "MISSING"
        latest = (manifest or {}).get("latest_nav_date") or (manifest or {}).get("latest_data_date") or latest_date
        note = (manifest or {}).get("warning") or self._mode_note(mode, "基金净值")
        return self._module(
            module="fund_nav",
            label="基金净值",
            source_mode=mode,
            latest_data_date=latest,
            record_count=record_count,
            coverage_ratio=1.0 if record_count else 0.0,
            can_drive_advice=mode == "REAL",
            risk_level=self._risk_for_mode(mode),
            note=note,
            source_breakdown={self._normalize_mode(key): int(value or 0) for key, value in source_count.items()} if source_count else {mode: record_count},
        )

    def _portfolio_snapshot_module(self) -> dict[str, Any]:
        row = self._table_stats("portfolio_snapshot", "snapshot_date")
        count = int(row.get("record_count") or 0)
        mode = "ESTIMATED" if count else "MISSING"
        return self._module(
            module="portfolio_snapshot",
            label="组合快照",
            source_mode=mode,
            latest_data_date=row.get("latest_data_date"),
            record_count=count,
            coverage_ratio=1.0 if count else 0.0,
            can_drive_advice=False,
            risk_level="LOW" if count else "MEDIUM",
            note="组合快照由本地持仓和估值生成，用于复盘参考。" if count else "尚未生成组合快照。",
        )

    def _review_loop_module(self) -> dict[str, Any]:
        counts = 0
        latest: str | None = None
        for table, date_col in (("review_task", "source_date"), ("decision_record", "decision_date"), ("decision_outcome", "measured_at")):
            row = self._table_stats(table, date_col)
            counts += int(row.get("record_count") or 0)
            latest = self._latest_date(latest, row.get("latest_data_date"))
        mode = "REAL" if counts else "MISSING"
        return self._module(
            module="review_loop",
            label="复盘闭环",
            source_mode=mode,
            latest_data_date=latest,
            record_count=counts,
            coverage_ratio=1.0 if counts else 0.0,
            can_drive_advice=False,
            risk_level="LOW" if counts else "MEDIUM",
            note="复盘闭环来自系统事项和用户决策记录，用于复盘，不代表外部行情数据。" if counts else "尚未沉淀重要事项、决策或 outcome。",
        )

    def _table_module(self, spec: ModuleSpec) -> dict[str, Any]:
        total = 0
        latest: str | None = None
        modes: dict[str, int] = {}
        for table, date_col, mode_col in spec.tables:
            if not self._table_exists(table):
                continue
            row = self.repo.fetch_one(
                f"""
                SELECT COUNT(*) AS record_count,
                       MAX({date_col}) AS latest_data_date
                FROM {table}
                """
            ) or {}
            total += int(row.get("record_count") or 0)
            latest = self._latest_date(latest, row.get("latest_data_date"))
            for mode_row in self.repo.fetch_all(
                f"""
                SELECT UPPER(COALESCE({mode_col}, 'MISSING')) AS source_mode,
                       COUNT(*) AS count
                FROM {table}
                GROUP BY UPPER(COALESCE({mode_col}, 'MISSING'))
                """
            ):
                mode = self._normalize_mode(mode_row.get("source_mode"))
                modes[mode] = modes.get(mode, 0) + int(mode_row.get("count") or 0)
        mode = self._dominant_mode(modes) if total else "MISSING"
        note = self._mode_note(mode, spec.label) if total else spec.default_missing_note
        return self._module(
            module=spec.key,
            label=spec.label,
            source_mode=mode,
            latest_data_date=latest,
            record_count=total,
            coverage_ratio=1.0 if total else 0.0,
            can_drive_advice=spec.can_drive_advice_when_real and mode == "REAL",
            risk_level=self._risk_for_mode(mode),
            note=note,
            source_breakdown=modes,
        )

    def _module(self, **kwargs: Any) -> dict[str, Any]:
        kwargs.setdefault("latest_data_date", None)
        kwargs.setdefault("coverage_ratio", None)
        kwargs.setdefault("source_breakdown", {kwargs["source_mode"]: kwargs["record_count"]})
        return kwargs

    def _summary(self, modules: list[dict[str, Any]]) -> dict[str, Any]:
        counts = {"REAL": 0, "ESTIMATED": 0, "SAMPLE": 0, "MISSING": 0, "MIXED": 0}
        latest: str | None = None
        for item in modules:
            mode = self._normalize_mode(item.get("source_mode"))
            counts[mode] = counts.get(mode, 0) + 1
            latest = self._latest_date(latest, item.get("latest_data_date"))
        non_zero_modes = [mode for mode, count in counts.items() if count > 0 and mode != "MIXED"]
        if counts.get("MIXED", 0) or len(non_zero_modes) > 1:
            overall = "MIXED"
        elif non_zero_modes:
            overall = non_zero_modes[0]
        else:
            overall = "MISSING"
        return {
            "overall_mode": overall,
            "real_count": counts.get("REAL", 0),
            "estimated_count": counts.get("ESTIMATED", 0),
            "sample_count": counts.get("SAMPLE", 0),
            "missing_count": counts.get("MISSING", 0),
            "mixed_count": counts.get("MIXED", 0),
            "latest_data_date": latest,
            "has_blocking_issue": counts.get("MISSING", 0) > 0,
            "module_count": len(modules),
        }


    def _latest_raw_manifest(self, dataset: str) -> dict[str, Any] | None:
        raw_dir = self.settings.data_dir / "raw" / dataset
        if not raw_dir.exists():
            return None
        manifests = sorted(raw_dir.glob("*_manifest.json"), key=lambda item: item.name, reverse=True)
        for manifest_path in manifests:
            try:
                return json.loads(manifest_path.read_text(encoding="utf-8")) | {"manifest_file": manifest_path.name}
            except Exception:
                continue
        return None

    def _mode_from_source_count(self, source_count: dict[str, Any] | None) -> str:
        if not source_count:
            return "MISSING"
        sample_count = int(source_count.get("sample") or 0)
        real_count = sum(int(value or 0) for key, value in source_count.items() if key.lower() != "sample")
        if real_count > 0 and sample_count > 0:
            return "MIXED"
        if real_count > 0:
            return "REAL"
        if sample_count > 0:
            return "SAMPLE"
        return "MISSING"

    def _table_exists(self, table: str) -> bool:
        row = self.repo.fetch_one("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
        return bool(row)

    def _table_stats(self, table: str, date_col: str) -> dict[str, Any]:
        if not self._table_exists(table):
            return {"record_count": 0, "latest_data_date": None}
        return self.repo.fetch_one(
            f"SELECT COUNT(*) AS record_count, MAX({date_col}) AS latest_data_date FROM {table}"
        ) or {"record_count": 0, "latest_data_date": None}

    def _partition_stats(self, base: Path, prefix: str) -> tuple[int, str | None]:
        if not base.exists():
            return 0, None
        files = list(base.glob("**/*.parquet"))
        dates: list[str] = []
        for path in files:
            for part in path.parts:
                if part.startswith(prefix):
                    dates.append(part.split("=", 1)[1])
        return len(files), max(dates) if dates else None

    def _normalize_mode(self, mode: Any) -> str:
        value = str(mode or "MISSING").upper()
        mapping = {
            "REAL": "REAL",
            "SAMPLE": "SAMPLE",
            "MIXED": "MIXED",
            "ESTIMATED": "ESTIMATED",
            "UNKNOWN": "MISSING",
            "MISSING": "MISSING",
        }
        return mapping.get(value, "MISSING")

    def _dominant_mode(self, modes: dict[str, int]) -> str:
        active = {mode: count for mode, count in modes.items() if count > 0}
        if not active:
            return "MISSING"
        if len(active) == 1:
            return next(iter(active))
        if active.get("REAL", 0) and not (active.get("SAMPLE", 0) or active.get("ESTIMATED", 0) or active.get("MISSING", 0)):
            return "REAL"
        return "MIXED"

    def _risk_for_mode(self, mode: str) -> str:
        if mode == "REAL":
            return "LOW"
        if mode in {"ESTIMATED", "SAMPLE", "MIXED"}:
            return "MEDIUM"
        return "HIGH"

    def _mode_note(self, mode: str, label: str) -> str:
        if mode == "REAL":
            return f"{label} 使用真实数据，可作为规则判断的重要输入。"
        if mode == "ESTIMATED":
            return f"{label} 主要为估算数据，可用于展示和低置信解释，不应单独触发高优先级建议。"
        if mode == "SAMPLE":
            return f"{label} 使用样本数据，仅用于功能演示，不应作为真实投资依据。"
        if mode == "MIXED":
            return f"{label} 包含真实、估算、样本或缺失数据，结论需结合明细谨慎使用。"
        return f"{label} 数据缺失，暂不能形成确定性结论。"

    def _latest_date(self, left: Any, right: Any) -> str | None:
        values = [str(value) for value in (left, right) if value]
        return max(values) if values else None
