from __future__ import annotations

import time
from dataclasses import dataclass
from multiprocessing import get_context
from multiprocessing.queues import Queue
from typing import Any

import duckdb
import pandas as pd

from app.core.asset_type import infer_asset_type
from app.core.config import get_settings
from app.repositories.sqlite_repo import SQLiteRepository

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
class QuoteResult:
    symbol: str
    name: str | None
    asset_type: str
    price: float | None
    price_time: str | None
    trade_date: str | None
    source_mode: str
    source_provider: str | None
    source_interface: str | None
    warning: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "asset_type": self.asset_type,
            "price": self.price,
            "price_time": self.price_time,
            "trade_date": self.trade_date,
            "source_mode": self.source_mode,
            "source_provider": self.source_provider,
            "source_interface": self.source_interface,
            "warning": self.warning,
        }


class QuoteService:
    def __init__(self, repo: SQLiteRepository | None = None) -> None:
        self.repo = repo or SQLiteRepository()
        self.settings = get_settings()

    def quote(self, raw_symbol: str) -> dict[str, Any]:
        symbol = self.normalize_symbol(raw_symbol)
        instrument = self._instrument(symbol)
        explicit_type = instrument.get("asset_type") if instrument else None
        asset_type = infer_asset_type(symbol, explicit=explicit_type)
        name = instrument.get("name") if instrument else None

        if asset_type in {"STOCK", "ETF"}:
            realtime = self._quote_realtime(symbol, asset_type)
            if realtime.price is not None:
                return realtime.to_dict()

        cached = self._quote_from_cache(symbol, asset_type, name)
        if cached.price is not None:
            return cached.to_dict()

        return QuoteResult(
            symbol=symbol,
            name=name or symbol,
            asset_type=asset_type,
            price=None,
            price_time=None,
            trade_date=None,
            source_mode="MISSING",
            source_provider=None,
            source_interface=None,
            warning="未找到真实实时报价或本地真实历史缓存，可手动录入临时价格。",
        ).to_dict()

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
    def normalize_symbol(raw_symbol: str) -> str:
        value = raw_symbol.strip().upper().replace("_", ".")
        if not value:
            return value
        if value.startswith("SH") and len(value) == 8:
            return f"{value[2:]}.SH"
        if value.startswith("SZ") and len(value) == 8:
            return f"{value[2:]}.SZ"
        if "." in value:
            code, suffix = value.split(".", 1)
            return f"{code}.{suffix}"
        if len(value) == 6 and value.isdigit():
            if value.startswith(("5", "6")):
                return f"{value}.SH"
            if value.startswith(("0", "1", "2", "3")):
                return f"{value}.SZ"
        return value

    def _instrument(self, symbol: str) -> dict[str, Any] | None:
        row = self.repo.fetch_one("SELECT * FROM instrument WHERE symbol = ?", (symbol,))
        return dict(row) if row else None

    def _quote_realtime(self, symbol: str, asset_type: str) -> QuoteResult:
        started = time.monotonic()
        try:
            raw = _invoke_realtime(timeout_seconds=8.0)
            item = _extract_spot_row(raw, symbol)
            if not item:
                raise RuntimeError("symbol not found in realtime source")
            price = _to_float(item.get("最新价") or item.get("最新") or item.get("close"))
            if price is None:
                raise RuntimeError("realtime source returned no price")
            name = str(item.get("名称") or item.get("name") or symbol)
            price_time = str(item.get("更新时间") or item.get("time") or "") or None
            return QuoteResult(
                symbol=symbol,
                name=name,
                asset_type=asset_type,
                price=price,
                price_time=price_time,
                trade_date=None,
                source_mode="REAL_QUOTE",
                source_provider="eastmoney",
                source_interface="stock_zh_a_spot_em",
                warning=None,
            )
        except Exception as exc:
            elapsed = int((time.monotonic() - started) * 1000)
            return QuoteResult(
                symbol=symbol,
                name=symbol,
                asset_type=asset_type,
                price=None,
                price_time=None,
                trade_date=None,
                source_mode="MISSING",
                source_provider="eastmoney",
                source_interface="stock_zh_a_spot_em",
                warning=(
                    "实时行情不可用，已降级到本地真实缓存；"
                    f"原因：{exc.__class__.__name__}，耗时 {elapsed}ms。"
                ),
            )

    def _quote_from_cache(self, symbol: str, asset_type: str, name: str | None) -> QuoteResult:
        if asset_type == "FUND":
            cached = self._latest_fund_nav(symbol)
            provider = "local_fund_nav"
            interface = "fund_nav"
        else:
            cached = self._latest_daily_bar(symbol)
            provider = "local_daily_bar"
            interface = "daily_bar"
        if not cached:
            return QuoteResult(
                symbol=symbol,
                name=name or symbol,
                asset_type=asset_type,
                price=None,
                price_time=None,
                trade_date=None,
                source_mode="MISSING",
                source_provider=provider,
                source_interface=interface,
                warning="本地没有可用的真实历史缓存。",
            )
        return QuoteResult(
            symbol=symbol,
            name=cached.get("name") or name or symbol,
            asset_type=asset_type,
            price=float(cached["price"]),
            price_time=None,
            trade_date=str(cached.get("trade_date") or cached.get("nav_date") or ""),
            source_mode="REAL_CACHED",
            source_provider=provider,
            source_interface=interface,
            warning="实时行情不可用，使用本地最新真实历史缓存；不代表盘中实时价格。",
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


def _real_filter(column: str) -> str:
    blocked = "', '".join(sorted(NON_REAL_SOURCES))
    return f"LOWER(COALESCE(CAST({column} AS VARCHAR), '')) NOT IN ('{blocked}')"


def _to_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _parquet_columns(parquet_glob: str) -> set[str]:
    with duckdb.connect(database=":memory:", read_only=False) as conn:
        rows = conn.execute(
            "DESCRIBE SELECT * FROM read_parquet(?, hive_partitioning = true) LIMIT 0",
            [parquet_glob],
        ).fetchall()
    return {str(row[0]) for row in rows}


def _realtime_child(queue: Queue) -> None:
    try:
        import akshare as ak  # type: ignore

        queue.put(("ok", ak.stock_zh_a_spot_em()))
    except Exception as exc:
        queue.put(("err", exc.__class__.__name__, str(exc)))


def _invoke_realtime(timeout_seconds: float) -> Any:
    ctx = get_context("fork")
    queue: Queue = ctx.Queue(maxsize=1)
    process = ctx.Process(target=_realtime_child, args=(queue,))
    process.daemon = True
    process.start()
    process.join(timeout_seconds)
    if process.is_alive():
        process.terminate()
        process.join(1)
        raise TimeoutError("stock_zh_a_spot_em timed out")
    if queue.empty():
        raise RuntimeError("stock_zh_a_spot_em exited without result")
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
    for code_col in ("代码", "symbol", "code"):
        if code_col in df.columns:
            matched = df[df[code_col].astype(str).str.upper().str.endswith(code)]
            if not matched.empty:
                return dict(matched.iloc[0])
    return None
