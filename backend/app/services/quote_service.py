from __future__ import annotations

import time
from dataclasses import dataclass, field
from multiprocessing import get_context
from multiprocessing.queues import Queue
from typing import Any

import duckdb
import pandas as pd

from app.core.asset_type import infer_asset_type
from app.core.config import get_settings
from app.repositories.sqlite_repo import SQLiteRepository

ALLOWED_ASSET_TYPES = {"STOCK", "ETF", "FUND"}
NON_REAL_SOURCES = {
    "sample",
    "estimated",
    "built_in_sample",
    "deterministic_estimate",
    "instrument_estimate",
    "mock",
    "demo",
}


@dataclass(frozen=True)
class QuoteAttempt:
    provider: str
    interface: str
    status: str
    elapsed_ms: int
    error_class: str | None = None
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "interface": self.interface,
            "status": self.status,
            "elapsed_ms": self.elapsed_ms,
            "error_class": self.error_class,
            "error_message": self.error_message,
        }


@dataclass(frozen=True)
class QuoteResult:
    symbol: str
    name: str | None
    asset_type: str
    price: float | None
    price_label: str
    price_time: str | None
    trade_date: str | None
    source_mode: str
    source_provider: str | None
    source_interface: str | None
    fallback_reason: str | None
    warning: str | None
    attempts: list[QuoteAttempt] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "asset_type": self.asset_type,
            "price": self.price,
            "price_label": self.price_label,
            "price_time": self.price_time,
            "trade_date": self.trade_date,
            "source_mode": self.source_mode,
            "source_provider": self.source_provider,
            "source_interface": self.source_interface,
            "fallback_reason": self.fallback_reason,
            "warning": self.warning,
            "attempts": [attempt.to_dict() for attempt in self.attempts],
        }


class QuoteService:
    def __init__(self, repo: SQLiteRepository | None = None) -> None:
        self.repo = repo or SQLiteRepository()
        self.settings = get_settings()

    def quote(self, raw_symbol: str, asset_type: str | None = None) -> dict[str, Any]:
        requested_type = _clean_asset_type(asset_type)
        lookup_symbol = self.normalize_symbol(raw_symbol, requested_type)
        instrument = self._instrument(lookup_symbol) or self._instrument(raw_symbol.strip().upper())
        instrument_type = instrument.get("asset_type") if instrument else None
        resolved_type = requested_type or infer_asset_type(lookup_symbol, explicit=instrument_type)
        symbol = self.normalize_symbol(raw_symbol, resolved_type)
        if symbol != lookup_symbol:
            instrument = self._instrument(symbol) or instrument
        name = instrument.get("name") if instrument else None

        if resolved_type == "STOCK":
            return self._quote_stock(symbol, name).to_dict()
        if resolved_type == "ETF":
            return self._quote_etf(symbol, name).to_dict()
        if resolved_type == "FUND":
            return self._quote_fund(symbol, name).to_dict()
        raise ValueError(f"unsupported asset_type: {resolved_type}")

    def search(self, keyword: str, limit: int = 20) -> list[dict[str, Any]]:
        value = keyword.strip()
        if not value:
            return []
        limit = max(1, min(limit, 50))
        pattern = f"%{value.upper()}%"
        rows = self.repo.fetch_all(
            """
            SELECT symbol, name, asset_type, market, exchange, status, source
            FROM instrument
            WHERE UPPER(symbol) LIKE ? OR UPPER(COALESCE(name, '')) LIKE ?
            ORDER BY CASE WHEN UPPER(symbol) = ? THEN 0 ELSE 1 END, symbol
            LIMIT ?
            """,
            (pattern, pattern, value.upper(), limit),
        )
        return [dict(row) for row in rows]

    @staticmethod
    def normalize_symbol(raw_symbol: str, asset_type: str | None = None) -> str:
        value = raw_symbol.strip().upper().replace("_", ".")
        if not value:
            return value
        normalized_type = _clean_asset_type(asset_type) if asset_type else None
        if normalized_type == "FUND":
            return value.split(".", 1)[0]
        if value.startswith("SH") and len(value) == 8:
            return f"{value[2:]}.SH"
        if value.startswith("SZ") and len(value) == 8:
            return f"{value[2:]}.SZ"
        if "." in value:
            code, suffix = value.split(".", 1)
            return f"{code}.{suffix}"
        if len(value) == 6 and value.isdigit():
            if normalized_type == "ETF":
                return f"{value}.SH" if value.startswith(("5", "6")) else f"{value}.SZ"
            if value.startswith(("5", "6")):
                return f"{value}.SH"
            if value.startswith(("0", "1", "2", "3")):
                return f"{value}.SZ"
        return value

    def _instrument(self, symbol: str) -> dict[str, Any] | None:
        row = self.repo.fetch_one("SELECT * FROM instrument WHERE symbol = ?", (symbol,))
        return dict(row) if row else None

    def _quote_stock(self, symbol: str, name: str | None) -> QuoteResult:
        realtime = self._quote_realtime(
            symbol=symbol,
            asset_type="STOCK",
            name=name,
            provider="eastmoney",
            interface="stock_zh_a_spot_em",
            child_target=_stock_spot_child,
            price_label="当前价",
            timeout_seconds=6.0,
        )
        if realtime.price is not None:
            return realtime
        cached = self._quote_from_cache(
            symbol=symbol,
            asset_type="STOCK",
            name=name,
            price_label="当前价",
            fallback_reason="realtime_provider_unavailable",
        )
        return self._merge_attempts(cached, realtime.attempts)

    def _quote_etf(self, symbol: str, name: str | None) -> QuoteResult:
        realtime = self._quote_realtime(
            symbol=symbol,
            asset_type="ETF",
            name=name,
            provider="eastmoney",
            interface="fund_etf_spot_em",
            child_target=_etf_spot_child,
            price_label="交易价格",
            timeout_seconds=6.0,
        )
        if realtime.price is not None:
            return realtime
        cached = self._quote_from_cache(
            symbol=symbol,
            asset_type="ETF",
            name=name,
            price_label="交易价格",
            fallback_reason="realtime_provider_unavailable",
        )
        return self._merge_attempts(cached, realtime.attempts)

    def _quote_fund(self, symbol: str, name: str | None) -> QuoteResult:
        realtime = self._quote_fund_nav(symbol=symbol, name=name, timeout_seconds=8.0)
        if realtime.price is not None:
            return realtime
        cached = self._quote_from_cache(
            symbol=symbol,
            asset_type="FUND",
            name=name,
            price_label="单位净值",
            fallback_reason="latest_nav_provider_unavailable",
        )
        return self._merge_attempts(cached, realtime.attempts)

    def _quote_realtime(
        self,
        *,
        symbol: str,
        asset_type: str,
        name: str | None,
        provider: str,
        interface: str,
        child_target: Any,
        price_label: str,
        timeout_seconds: float,
    ) -> QuoteResult:
        started = time.monotonic()
        try:
            raw = _invoke_child(child_target, timeout_seconds=timeout_seconds)
            item = _extract_spot_row(raw, symbol)
            if not item:
                raise RuntimeError("symbol not found in realtime source")
            price = _to_float(
                item.get("最新价")
                or item.get("最新")
                or item.get("close")
                or item.get("最新净值")
                or item.get("现价")
            )
            if price is None:
                raise RuntimeError("realtime source returned no price")
            resolved_name = str(item.get("名称") or item.get("name") or name or symbol)
            price_time = str(item.get("更新时间") or item.get("time") or "") or None
            elapsed = int((time.monotonic() - started) * 1000)
            return QuoteResult(
                symbol=symbol,
                name=resolved_name,
                asset_type=asset_type,
                price=price,
                price_label=price_label,
                price_time=price_time,
                trade_date=None,
                source_mode="REAL_QUOTE",
                source_provider=provider,
                source_interface=interface,
                fallback_reason=None,
                warning=None,
                attempts=[QuoteAttempt(provider, interface, "ok", elapsed)],
            )
        except Exception as exc:
            elapsed = int((time.monotonic() - started) * 1000)
            return QuoteResult(
                symbol=symbol,
                name=name or symbol,
                asset_type=asset_type,
                price=None,
                price_label=price_label,
                price_time=None,
                trade_date=None,
                source_mode="MISSING",
                source_provider=provider,
                source_interface=interface,
                fallback_reason="realtime_provider_unavailable",
                warning=(
                    f"{price_label}真实源不可用，已降级到本地真实缓存；"
                    f"原因：{exc.__class__.__name__}。"
                ),
                attempts=[
                    QuoteAttempt(
                        provider,
                        interface,
                        "failed",
                        elapsed,
                        exc.__class__.__name__,
                        str(exc),
                    )
                ],
            )

    def _quote_fund_nav(
        self,
        *,
        symbol: str,
        name: str | None,
        timeout_seconds: float,
    ) -> QuoteResult:
        provider = "eastmoney_ttfund"
        interface = "fund_open_fund_info_em"
        started = time.monotonic()
        try:
            raw = _invoke_child(_fund_nav_child, symbol, timeout_seconds=timeout_seconds)
            item = _extract_latest_fund_nav(raw)
            price = _to_float(item.get("单位净值") or item.get("净值") or item.get("nav"))
            if price is None:
                raise RuntimeError("fund nav source returned no unit nav")
            trade_date_value = item.get("净值日期") or item.get("日期") or item.get("nav_date")
            trade_date = str(trade_date_value or "") or None
            elapsed = int((time.monotonic() - started) * 1000)
            return QuoteResult(
                symbol=symbol,
                name=name or symbol,
                asset_type="FUND",
                price=price,
                price_label="单位净值",
                price_time=None,
                trade_date=trade_date,
                source_mode="REAL_QUOTE",
                source_provider=provider,
                source_interface=interface,
                fallback_reason=None,
                warning=None,
                attempts=[QuoteAttempt(provider, interface, "ok", elapsed)],
            )
        except Exception as exc:
            elapsed = int((time.monotonic() - started) * 1000)
            return QuoteResult(
                symbol=symbol,
                name=name or symbol,
                asset_type="FUND",
                price=None,
                price_label="单位净值",
                price_time=None,
                trade_date=None,
                source_mode="MISSING",
                source_provider=provider,
                source_interface=interface,
                fallback_reason="latest_nav_provider_unavailable",
                warning=(
                    "最新单位净值真实源不可用，已降级到本地 fund_nav 真实缓存；"
                    f"原因：{exc.__class__.__name__}。"
                ),
                attempts=[
                    QuoteAttempt(
                        provider,
                        interface,
                        "failed",
                        elapsed,
                        exc.__class__.__name__,
                        str(exc),
                    )
                ],
            )

    def _quote_from_cache(
        self,
        *,
        symbol: str,
        asset_type: str,
        name: str | None,
        price_label: str,
        fallback_reason: str,
    ) -> QuoteResult:
        if asset_type == "FUND":
            cached = self._latest_fund_nav(symbol)
            provider = "local_fund_nav"
            interface = "fund_nav"
            warning = "最新单位净值真实源不可用，使用本地最新真实净值缓存。"
        else:
            cached = self._latest_daily_bar(symbol)
            provider = "local_daily_bar"
            interface = "daily_bar"
            warning = "实时行情不可用，使用本地最新真实历史缓存；不代表盘中实时价格。"
        if not cached:
            return QuoteResult(
                symbol=symbol,
                name=name or symbol,
                asset_type=asset_type,
                price=None,
                price_label=price_label,
                price_time=None,
                trade_date=None,
                source_mode="MISSING",
                source_provider=provider,
                source_interface=interface,
                fallback_reason=fallback_reason,
                warning="没有可用的真实报价或本地真实历史缓存，可手动录入临时价格。",
            )
        return QuoteResult(
            symbol=symbol,
            name=cached.get("name") or name or symbol,
            asset_type=asset_type,
            price=float(cached["price"]),
            price_label=price_label,
            price_time=None,
            trade_date=str(cached.get("trade_date") or cached.get("nav_date") or ""),
            source_mode="REAL_CACHED",
            source_provider=provider,
            source_interface=interface,
            fallback_reason=fallback_reason,
            warning=warning,
        )

    def _latest_daily_bar(self, symbol: str) -> dict[str, Any] | None:
        base = self.settings.data_dir / "parquet" / "daily_bar"
        if not base.exists() or not any(base.rglob("*.parquet")):
            return None
        parquet_glob = str(base / "**" / "*.parquet")
        columns = _parquet_columns(parquet_glob)
        filters = ["symbol = ?"]
        if "source" in columns:
            filters.append(_real_filter("source"))
        if "source_mode" in columns:
            filters.append(_real_filter("source_mode"))
        name_expr = "name" if "name" in columns else "NULL AS name"
        sql = f"""
            SELECT CAST(trade_date AS VARCHAR) AS trade_date, {name_expr}, close AS price
            FROM read_parquet(?, hive_partitioning = true)
            WHERE {' AND '.join(filters)}
            ORDER BY trade_date DESC
            LIMIT 1
        """
        with duckdb.connect(database=":memory:", read_only=False) as conn:
            row = conn.execute(sql, [parquet_glob, symbol]).fetchone()
            cols = [desc[0] for desc in conn.description]
        return dict(zip(cols, row, strict=True)) if row else None

    def _latest_fund_nav(self, symbol: str) -> dict[str, Any] | None:
        base = self.settings.data_dir / "parquet" / "fund_nav"
        if not base.exists() or not any(base.rglob("*.parquet")):
            return None
        parquet_glob = str(base / "**" / "*.parquet")
        columns = _parquet_columns(parquet_glob)
        price_col = "nav" if "nav" in columns else "unit_nav"
        filters = ["symbol = ?"]
        if "source" in columns:
            filters.append(_real_filter("source"))
        if "source_mode" in columns:
            filters.append(_real_filter("source_mode"))
        name_expr = "name" if "name" in columns else "NULL AS name"
        sql = f"""
            SELECT CAST(nav_date AS VARCHAR) AS nav_date, {name_expr}, {price_col} AS price
            FROM read_parquet(?, hive_partitioning = true)
            WHERE {' AND '.join(filters)}
            ORDER BY nav_date DESC
            LIMIT 1
        """
        with duckdb.connect(database=":memory:", read_only=False) as conn:
            row = conn.execute(sql, [parquet_glob, symbol]).fetchone()
            cols = [desc[0] for desc in conn.description]
        return dict(zip(cols, row, strict=True)) if row else None

    @staticmethod
    def _merge_attempts(result: QuoteResult, attempts: list[QuoteAttempt]) -> QuoteResult:
        return QuoteResult(
            symbol=result.symbol,
            name=result.name,
            asset_type=result.asset_type,
            price=result.price,
            price_label=result.price_label,
            price_time=result.price_time,
            trade_date=result.trade_date,
            source_mode=result.source_mode,
            source_provider=result.source_provider,
            source_interface=result.source_interface,
            fallback_reason=result.fallback_reason,
            warning=result.warning,
            attempts=[*attempts, *result.attempts],
        )


def _clean_asset_type(asset_type: str | None) -> str | None:
    if asset_type is None or asset_type == "":
        return None
    value = asset_type.strip().upper()
    if value not in ALLOWED_ASSET_TYPES:
        raise ValueError(f"asset_type must be one of {sorted(ALLOWED_ASSET_TYPES)}")
    return value


def _real_filter(column: str) -> str:
    blocked = "', '".join(sorted(NON_REAL_SOURCES))
    return f"LOWER(COALESCE(CAST({column} AS VARCHAR), '')) NOT IN ('{blocked}')"


def _to_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        parsed = float(value)
        if pd.isna(parsed):
            return None
        return parsed
    except (TypeError, ValueError):
        return None


def _parquet_columns(parquet_glob: str) -> set[str]:
    with duckdb.connect(database=":memory:", read_only=False) as conn:
        rows = conn.execute(
            "DESCRIBE SELECT * FROM read_parquet(?, hive_partitioning = true) LIMIT 0",
            [parquet_glob],
        ).fetchall()
    return {str(row[0]) for row in rows}


def _stock_spot_child(queue: Queue) -> None:
    try:
        import akshare as ak  # type: ignore

        queue.put(("ok", ak.stock_zh_a_spot_em()))
    except Exception as exc:
        queue.put(("err", exc.__class__.__name__, str(exc)))


def _etf_spot_child(queue: Queue) -> None:
    try:
        import akshare as ak  # type: ignore

        queue.put(("ok", ak.fund_etf_spot_em()))
    except Exception as exc:
        queue.put(("err", exc.__class__.__name__, str(exc)))


def _fund_nav_child(queue: Queue, symbol: str) -> None:
    try:
        import akshare as ak  # type: ignore

        queue.put(("ok", ak.fund_open_fund_info_em(symbol=symbol, indicator="单位净值走势")))
    except Exception as exc:
        queue.put(("err", exc.__class__.__name__, str(exc)))


def _invoke_child(child_target: Any, *args: Any, timeout_seconds: float) -> Any:
    ctx = get_context("fork")
    queue: Queue = ctx.Queue(maxsize=1)
    process = ctx.Process(target=child_target, args=(queue, *args))
    process.daemon = True
    process.start()
    process.join(timeout_seconds)
    if process.is_alive():
        process.terminate()
        process.join(1)
        raise TimeoutError(f"{child_target.__name__} timed out")
    if queue.empty():
        raise RuntimeError(f"{child_target.__name__} exited without result")
    status, *payload = queue.get()
    if status == "ok":
        return payload[0]
    error_name, message = payload
    raise RuntimeError(f"{error_name}: {message}")


def _extract_spot_row(raw: Any, symbol: str) -> dict[str, Any] | None:
    df = pd.DataFrame(raw)
    if df.empty:
        return None
    code = symbol.split(".", 1)[0]
    for code_col in ("代码", "symbol", "code", "证券代码", "基金代码"):
        if code_col in df.columns:
            matched = df[df[code_col].astype(str).str.upper().str.endswith(code)]
            if not matched.empty:
                return dict(matched.iloc[0])
    return None


def _extract_latest_fund_nav(raw: Any) -> dict[str, Any]:
    df = pd.DataFrame(raw)
    if df.empty:
        raise RuntimeError("fund nav source returned empty dataframe")
    date_col = "净值日期" if "净值日期" in df.columns else "日期"
    if date_col in df.columns:
        df = df.sort_values(date_col)
    return dict(df.iloc[-1])
