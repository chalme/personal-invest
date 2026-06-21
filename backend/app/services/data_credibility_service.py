from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.repositories.sqlite_repo import SQLiteRepository


@dataclass(frozen=True)
class ModuleSpec:
    key: str
    label: str
    tables: tuple[tuple[str, str, str], ...]
    default_missing_note: str
    can_drive_advice_when_real: bool = True


class DataCredibilityService:
    """Aggregate data source credibility across analysis modules."""

    DAILY_FRESHNESS_MODULES = {"market_data", "daily_bar", "fund_nav"}
    NON_REAL_SOURCE_KEYS = {
        "sample",
        "estimated",
        "built_in_sample",
        "deterministic_estimate",
        "instrument_estimate",
        "mock",
        "demo",
    }
    NON_REAL_MODES = {"SAMPLE", "ESTIMATED"}
    REAL_CACHE_KEYS = {"akshare_cached", "real_cached", "historical_parquet"}

    def __init__(self, repo: SQLiteRepository | None = None) -> None:
        self.repo = repo or SQLiteRepository()
        self.settings = get_settings()

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
        manifest = self._latest_raw_manifest("market")
        return self._manifest_module(
            module="market_data",
            label="市场行情",
            manifest=manifest,
            latest_fallback_key="latest_trade_date",
            default_missing_note="尚未发现行情数据来源记录，请先执行每日更新。",
        )

    def _daily_bar_module(self) -> dict[str, Any]:
        base = self.settings.data_dir / "parquet" / "daily_bar"
        file_count, latest_date = self._partition_stats(base, "trade_date=")
        manifest = self._latest_raw_manifest("market")
        module = self._manifest_module(
            module="daily_bar",
            label="行情日线",
            manifest=manifest,
            latest_fallback_key="latest_trade_date",
            default_missing_note="尚未发现行情日线数据，请先执行每日更新。",
        )
        if file_count <= 0:
            module.update(
                {
                    "source_mode": "MISSING",
                    "latest_data_date": None,
                    "record_count": 0,
                    "coverage_ratio": 0.0,
                    "can_drive_advice": False,
                    "risk_level": "HIGH",
                }
            )
        else:
            module["latest_data_date"] = module.get("latest_data_date") or latest_date
            module["record_count"] = max(int(module.get("record_count") or 0), file_count)
        return self._with_freshness(module)

    def _manifest_module(
        self,
        *,
        module: str,
        label: str,
        manifest: dict[str, Any] | None,
        latest_fallback_key: str,
        default_missing_note: str,
    ) -> dict[str, Any]:
        if not manifest:
            return self._module(
                module=module,
                label=label,
                source_mode="MISSING",
                latest_data_date=None,
                record_count=0,
                coverage_ratio=0.0,
                can_drive_advice=False,
                risk_level="HIGH",
                note=default_missing_note,
                source_breakdown={"MISSING": 0},
            )
        source_count = dict(manifest.get("source_count") or {})
        mode = self._normalize_mode(manifest.get("source_mode"))
        if mode == "MISSING":
            mode = self._mode_from_source_count(source_count)
        record_count = int(manifest.get("rows") or 0)
        latest = manifest.get("latest_data_date") or manifest.get(latest_fallback_key)
        note = manifest.get("warning") or self._mode_note(mode, label)
        module_result = self._module(
            module=module,
            label=label,
            source_mode=mode,
            latest_data_date=latest,
            record_count=record_count,
            coverage_ratio=1.0 if record_count else 0.0,
            can_drive_advice=mode == "REAL",
            risk_level=self._risk_for_mode(mode),
            note=note,
            warning=manifest.get("warning"),
            source_breakdown={
                self._normalize_mode(key): int(value or 0) for key, value in source_count.items()
            }
            if source_count
            else {mode: record_count},
            provider_count=dict(manifest.get("provider_count") or {}),
            interface_count=dict(manifest.get("interface_count") or {}),
            missing_field_count=dict(manifest.get("missing_field_count") or {}),
            asset_source_status=dict(manifest.get("asset_source_status") or {}),
            asset_missing_fields=dict(manifest.get("asset_missing_fields") or {}),
            provider_error_count=dict(manifest.get("provider_error_count") or {}),
            error_category_count=dict(manifest.get("error_category_count") or {}),
            provider_disabled=list(manifest.get("provider_disabled") or []),
            asset_fallback_reason=dict(manifest.get("asset_fallback_reason") or {}),
        )
        return self._with_freshness(module_result)

    def _fund_nav_module(self) -> dict[str, Any]:
        base = self.settings.data_dir / "parquet" / "fund_nav"
        file_count, latest_date = self._partition_stats(base, "nav_date=")
        module = self._manifest_module(
            module="fund_nav",
            label="基金净值",
            manifest=self._latest_raw_manifest("fund"),
            latest_fallback_key="latest_nav_date",
            default_missing_note="尚未发现场外基金净值数据。",
        )
        if file_count > 0 and not module.get("latest_data_date"):
            module["latest_data_date"] = latest_date
        return self._with_freshness(module)

    def _portfolio_snapshot_module(self) -> dict[str, Any]:
        row = self._table_stats("portfolio_snapshot", "snapshot_date")
        count = int(row.get("record_count") or 0)
        mode = "REAL" if count else "MISSING"
        return self._module(
            module="portfolio_snapshot",
            label="组合快照",
            source_mode=mode,
            latest_data_date=row.get("latest_data_date"),
            record_count=count,
            coverage_ratio=1.0 if count else 0.0,
            can_drive_advice=False,
            risk_level="LOW" if count else "MEDIUM",
            note="组合快照由本地持仓与价格/净值结果生成，用于复盘参考。"
            if count
            else "尚未生成组合快照。",
        )

    def _review_loop_module(self) -> dict[str, Any]:
        counts = 0
        latest: str | None = None
        for table, date_col in (
            ("review_task", "source_date"),
            ("decision_record", "decision_date"),
            ("decision_outcome", "measured_at"),
        ):
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
            note="复盘闭环来自系统事项和用户决策记录，用于复盘，不代表外部行情数据。"
            if counts
            else "尚未沉淀重要事项、决策或 outcome。",
        )

    def _table_module(self, spec: ModuleSpec) -> dict[str, Any]:
        total = 0
        latest: str | None = None
        modes: dict[str, int] = {}
        for table, date_col, mode_col in spec.tables:
            if not self._table_exists(table):
                continue
            row = (
                self.repo.fetch_one(
                    f"""
                SELECT COUNT(*) AS record_count,
                       MAX({date_col}) AS latest_data_date
                FROM {table}
                """
                )
                or {}
            )
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
        kwargs.setdefault(
            "expected_latest_trade_date", self._expected_latest_trade_date().isoformat()
        )
        kwargs.setdefault("trade_calendar_source_mode", "ESTIMATED")
        kwargs.setdefault("freshness_status", "NOT_APPLICABLE")
        kwargs.setdefault("stale_days", None)
        kwargs.setdefault("warning", None)
        return kwargs

    def _summary(self, modules: list[dict[str, Any]]) -> dict[str, Any]:
        counts = {"REAL": 0, "ESTIMATED": 0, "SAMPLE": 0, "MISSING": 0, "MIXED": 0}
        latest: str | None = None
        freshness_modules = [
            item for item in modules if item.get("freshness_status") != "NOT_APPLICABLE"
        ]
        stale_count = 0
        missing_freshness_count = 0
        real_cached_count = 0
        cannot_drive_count = 0
        for item in modules:
            mode = self._normalize_mode(item.get("source_mode"))
            counts[mode] = counts.get(mode, 0) + 1
            latest = self._latest_date(latest, item.get("latest_data_date"))
            if item.get("freshness_status") == "STALE":
                stale_count += 1
            if item.get("freshness_status") == "MISSING":
                missing_freshness_count += 1
            if not item.get("can_drive_advice"):
                cannot_drive_count += 1
            real_cached_count += self._module_cached_count(item)
        pollution = self._raw_manifest_pollution_summary()
        non_zero_modes = [
            mode
            for mode, count in counts.items()
            if count > 0 and mode not in {"MIXED", "SAMPLE", "ESTIMATED"}
        ]
        if counts.get("SAMPLE", 0) or counts.get("ESTIMATED", 0):
            overall = "HISTORICAL_POLLUTION"
        elif counts.get("MIXED", 0):
            overall = "DEGRADED"
        elif len(non_zero_modes) > 1:
            overall = "DEGRADED"
        elif non_zero_modes:
            overall = non_zero_modes[0]
        else:
            overall = "MISSING"
        if stale_count > 0:
            freshness_status = "STALE"
        elif missing_freshness_count > 0:
            freshness_status = "MISSING"
        elif freshness_modules:
            freshness_status = "FRESH"
        else:
            freshness_status = "NOT_APPLICABLE"
        expected_latest_trade_date = self._expected_latest_trade_date().isoformat()
        freshness_warning = self._freshness_summary_warning(
            freshness_status,
            stale_count,
            missing_freshness_count,
            pollution.get("manifest_polluted_file_count", 0),
        )
        return {
            "overall_mode": overall,
            "real_count": counts.get("REAL", 0),
            "real_cached_count": real_cached_count,
            "estimated_count": counts.get("ESTIMATED", 0),
            "sample_count": counts.get("SAMPLE", 0),
            "missing_count": counts.get("MISSING", 0),
            "mixed_count": counts.get("MIXED", 0),
            "historical_pollution_count": counts.get("ESTIMATED", 0)
            + counts.get("SAMPLE", 0)
            + pollution.get("manifest_polluted_file_count", 0),
            "manifest_polluted_file_count": pollution.get("manifest_polluted_file_count", 0),
            "manifest_polluted_record_count": pollution.get("manifest_polluted_record_count", 0),
            "latest_data_date": latest,
            "expected_latest_trade_date": expected_latest_trade_date,
            "trade_calendar_source_mode": "ESTIMATED",
            "freshness_status": freshness_status,
            "stale_count": stale_count,
            "missing_freshness_count": missing_freshness_count,
            "cannot_drive_advice_count": cannot_drive_count,
            "can_drive_advice_count": sum(1 for item in modules if item.get("can_drive_advice")),
            "warning": freshness_warning,
            "has_blocking_issue": counts.get("MISSING", 0) > 0
            or pollution.get("manifest_polluted_file_count", 0) > 0,
            "module_count": len(modules),
        }

    def _with_freshness(self, module: dict[str, Any]) -> dict[str, Any]:
        if module.get("module") not in self.DAILY_FRESHNESS_MODULES:
            return module
        latest = self._parse_iso_date(module.get("latest_data_date"))
        expected = self._expected_latest_trade_date()
        source_mode = self._normalize_mode(module.get("source_mode"))
        if source_mode == "MISSING" or latest is None:
            status = "MISSING"
            stale_days: int | None = None
        elif latest >= expected:
            status = "FRESH"
            stale_days = 0
        else:
            status = "STALE"
            stale_days = self._business_day_gap(latest, expected)
        module["expected_latest_trade_date"] = expected.isoformat()
        module["trade_calendar_source_mode"] = "ESTIMATED"
        module["freshness_status"] = status
        module["stale_days"] = stale_days
        module["can_drive_advice"] = (
            bool(module.get("can_drive_advice")) and status == "FRESH" and source_mode == "REAL"
        )
        if status == "STALE":
            module["risk_level"] = (
                "MEDIUM"
                if module.get("risk_level") == "LOW"
                else module.get("risk_level", "MEDIUM")
            )
        if status == "MISSING":
            module["risk_level"] = "HIGH"
        module["warning"] = self._freshness_warning(module)
        if module["warning"]:
            module["note"] = self._merge_note_and_warning(
                str(module.get("note") or ""), module["warning"]
            )
        return module

    def _expected_latest_trade_date(self, today: date | None = None) -> date:
        current = today or date.today()
        while current.weekday() >= 5:
            current -= timedelta(days=1)
        return current

    def _business_day_gap(self, latest: date, expected: date) -> int:
        if latest >= expected:
            return 0
        days = 0
        current = latest + timedelta(days=1)
        while current <= expected:
            if current.weekday() < 5:
                days += 1
            current += timedelta(days=1)
        return days

    def _parse_iso_date(self, value: Any) -> date | None:
        if not value:
            return None
        text = str(value)[:10]
        try:
            return datetime.strptime(text, "%Y-%m-%d").date()
        except ValueError:
            return None

    def _freshness_warning(self, module: dict[str, Any]) -> str | None:
        status = module.get("freshness_status")
        label = module.get("label") or module.get("module") or "数据"
        expected = module.get("expected_latest_trade_date")
        latest = module.get("latest_data_date") or "暂无"
        stale_days = module.get("stale_days")
        calendar_note = "最近交易日按工作日估算，未纳入法定节假日或临时休市。"
        source_warning = module.get("warning")
        if status == "FRESH":
            return source_warning or calendar_note
        if status == "STALE":
            return (
                f"{label}最新日期 {latest}，落后预期最近交易日 {expected} "
                f"约 {stale_days} 个交易日；{calendar_note}"
            )
        if status == "MISSING":
            return f"{label}缺少可判断新鲜度的数据日期，不能驱动高置信建议；{calendar_note}"
        return source_warning

    def _freshness_summary_warning(
        self,
        status: str,
        stale_count: int,
        missing_count: int,
        manifest_polluted_file_count: int = 0,
    ) -> str | None:
        calendar_note = "最近交易日按工作日估算，未纳入法定节假日或临时休市。"
        pollution_note = (
            f"已发现 {manifest_polluted_file_count} 个历史污染 manifest，"
            "已从当前可信度主视图排除。"
            if manifest_polluted_file_count > 0
            else None
        )
        if status == "STALE":
            base = f"{stale_count} 个日频数据模块已落后预期交易日；{calendar_note}"
            return f"{base} {pollution_note}" if pollution_note else base
        if status == "MISSING":
            base = f"{missing_count} 个日频数据模块缺少可判断新鲜度的数据日期；{calendar_note}"
            return f"{base} {pollution_note}" if pollution_note else base
        if status == "FRESH":
            return f"{calendar_note} {pollution_note}" if pollution_note else calendar_note
        return pollution_note

    def _merge_note_and_warning(self, note: str, warning: str | None) -> str:
        if not warning:
            return note
        if not note:
            return warning
        if warning in note:
            return note
        return f"{note} {warning}"

    def _latest_raw_manifest(self, dataset: str) -> dict[str, Any] | None:
        raw_dir = self.settings.data_dir / "raw" / dataset
        if not raw_dir.exists():
            return None
        manifests = sorted(
            raw_dir.glob("*_manifest.json"), key=lambda item: item.name, reverse=True
        )
        for manifest_path in manifests:
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8")) | {
                    "manifest_file": manifest_path.name
                }
            except Exception:
                continue
            if self._manifest_has_non_real_pollution(manifest):
                continue
            return manifest
        return None

    def _raw_manifest_pollution_summary(self) -> dict[str, int]:
        raw_dir = self.settings.data_dir / "raw"
        polluted_files = 0
        polluted_records = 0
        if not raw_dir.exists():
            return {
                "manifest_polluted_file_count": 0,
                "manifest_polluted_record_count": 0,
            }
        for manifest_path in raw_dir.glob("**/*_manifest.json"):
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except Exception:
                polluted_files += 1
                polluted_records += 1
                continue
            record_count = self._manifest_non_real_record_count(manifest)
            if self._manifest_has_non_real_pollution(manifest):
                polluted_files += 1
                polluted_records += max(record_count, 1)
        return {
            "manifest_polluted_file_count": polluted_files,
            "manifest_polluted_record_count": polluted_records,
        }

    def _manifest_has_non_real_pollution(self, manifest: dict[str, Any]) -> bool:
        mode = self._normalize_mode(manifest.get("source_mode"))
        return mode in self.NON_REAL_MODES or self._manifest_non_real_record_count(manifest) > 0

    def _manifest_non_real_record_count(self, manifest: dict[str, Any]) -> int:
        total = 0
        for key, value in dict(manifest.get("source_count") or {}).items():
            if str(key).lower() in self.NON_REAL_SOURCE_KEYS:
                total += int(value or 0)
        return total

    def _module_cached_count(self, module: dict[str, Any]) -> int:
        provider_count = dict(module.get("provider_count") or {})
        source_breakdown = dict(module.get("source_breakdown") or {})
        asset_source_status = dict(module.get("asset_source_status") or {})
        provider_total = sum(
            int(value or 0)
            for key, value in provider_count.items()
            if str(key).lower() in self.REAL_CACHE_KEYS
        )
        source_total = sum(
            int(value or 0)
            for key, value in source_breakdown.items()
            if str(key).lower() in self.REAL_CACHE_KEYS
        )
        asset_total = sum(
            1
            for status in asset_source_status.values()
            if str(status).lower() in self.REAL_CACHE_KEYS
            or "cached" in str(status).lower()
        )
        return max(provider_total, source_total, asset_total)

    def _mode_from_source_count(self, source_count: dict[str, Any] | None) -> str:
        if not source_count:
            return "MISSING"
        non_record_keys = {"missing", "unknown", "none", "null"}
        sample_count = sum(
            int(value or 0)
            for key, value in source_count.items()
            if key.lower() in self.NON_REAL_SOURCE_KEYS
        )
        real_count = sum(
            int(value or 0)
            for key, value in source_count.items()
            if key.lower() not in self.NON_REAL_SOURCE_KEYS | non_record_keys
        )
        if real_count > 0 and sample_count > 0:
            return "MIXED"
        if real_count > 0:
            return "REAL"
        if sample_count > 0:
            return "SAMPLE"
        return "MISSING"

    def _table_exists(self, table: str) -> bool:
        row = self.repo.fetch_one(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
        )
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
            "AKSHARE": "REAL",
            "AKSHARE_CACHED": "REAL",
            "REAL_CACHED": "REAL",
            "SAMPLE": "SAMPLE",
            "MIXED": "MIXED",
            "ESTIMATED": "ESTIMATED",
            "HISTORICAL_POLLUTION": "HISTORICAL_POLLUTION",
            "DEGRADED": "DEGRADED",
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
        if active.get("REAL", 0) and not (
            active.get("SAMPLE", 0) or active.get("ESTIMATED", 0) or active.get("MISSING", 0)
        ):
            return "REAL"
        return "MIXED"

    def _risk_for_mode(self, mode: str) -> str:
        if mode == "REAL":
            return "LOW"
        if mode == "MIXED" or mode == "DEGRADED":
            return "MEDIUM"
        if mode in {"ESTIMATED", "SAMPLE", "HISTORICAL_POLLUTION"}:
            return "HIGH"
        return "HIGH"

    def _mode_note(self, mode: str, label: str) -> str:
        if mode == "REAL":
            return f"{label} 使用真实数据，可作为规则判断的重要输入。"
        if mode == "ESTIMATED":
            return f"{label} 命中历史估算数据，属于待清理污染，不可作为正常投资判断输入。"
        if mode == "SAMPLE":
            return f"{label} 命中历史样本数据，属于待清理污染，不可作为正常投资判断输入。"
        if mode == "MIXED" or mode == "DEGRADED":
            return f"{label} 处于降级状态，请查看设置页治理明细。"
        if mode == "HISTORICAL_POLLUTION":
            return f"{label} 命中历史非真实污染，已排除为正常建议输入。"
        return f"{label} 数据缺失，暂不能形成确定性结论。"

    def _latest_date(self, left: Any, right: Any) -> str | None:
        values = [str(value) for value in (left, right) if value]
        return max(values) if values else None
