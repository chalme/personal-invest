from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from multiprocessing import get_context
from multiprocessing.queues import Queue
from typing import Any

import pandas as pd

INDEX_SYMBOLS = {"000001.SH", "399001.SZ", "399006.SZ", "000300.SH", "000905.SH"}
ETF_PREFIXES = ("51", "15", "16")
STANDARD_DAILY_BAR_COLUMNS = [
    "trade_date",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "amount",
    "turnover_rate",
    "pct_chg",
    "pe_ttm",
    "pb_mrq",
    "ps_ttm",
    "pcf_ncf_ttm",
    "trade_status",
    "is_st",
    "symbol",
    "name",
    "source",
    "source_mode",
    "source_provider",
    "source_interface",
    "missing_fields",
    "derived_fields",
    "fallback_reason",
]


@dataclass(frozen=True)
class ProviderSpec:
    provider: str
    interface: str
    asset_kinds: tuple[str, ...]
    query_symbol: Callable[[str], str]
    call: Callable[[Any, str, str, str], Any]


@dataclass
class ProviderAttempt:
    provider: str
    interface: str
    status: str
    elapsed_ms: int
    rows: int = 0
    latest_date: str | None = None
    error_class: str | None = None
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "interface": self.interface,
            "status": self.status,
            "rows": self.rows,
            "latest_date": self.latest_date,
            "error_class": self.error_class,
            "error_message": self.error_message,
            "elapsed_ms": self.elapsed_ms,
        }


@dataclass
class ProviderResult:
    frame: pd.DataFrame
    provider: str
    interface: str
    missing_fields: list[str]
    derived_fields: list[str]
    fallback_reason: str | None
    attempts: list[ProviderAttempt]


@dataclass
class ProviderRuntime:
    timeout_seconds: float = 12.0
    retries: int = 1
    failure_threshold: int = 3
    disabled: set[str] = field(default_factory=set)
    consecutive_failures: dict[str, int] = field(default_factory=dict)
    error_count: dict[str, int] = field(default_factory=dict)
    provider_error_count: dict[str, int] = field(default_factory=dict)

    def record_failure(self, provider: str, category: str) -> None:
        self.error_count[category] = self.error_count.get(category, 0) + 1
        self.provider_error_count[provider] = self.provider_error_count.get(provider, 0) + 1
        failures = self.consecutive_failures.get(provider, 0) + 1
        self.consecutive_failures[provider] = failures
        if failures >= self.failure_threshold:
            self.disabled.add(provider)

    def record_success(self, provider: str) -> None:
        self.consecutive_failures[provider] = 0


class ProviderFetchError(Exception):
    def __init__(self, category: str, message: str) -> None:
        super().__init__(message)
        self.category = category
        self.message = message


def _code(symbol: str) -> str:
    return symbol.split(".", 1)[0]


def to_tx_symbol(symbol: str) -> str:
    code = _code(symbol)
    suffix = symbol.split(".", 1)[1].upper() if "." in symbol else ""
    if suffix == "SH":
        return f"sh{code}"
    if suffix == "SZ":
        return f"sz{code}"
    if code.startswith(("6", "5")):
        return f"sh{code}"
    return f"sz{code}"


def to_baostock_symbol(symbol: str) -> str:
    code = _code(symbol)
    suffix = symbol.split(".", 1)[1].upper() if "." in symbol else ""
    if suffix == "SH":
        market = "sh"
    elif suffix == "SZ":
        market = "sz"
    elif code.startswith("6"):
        market = "sh"
    elif code.startswith(("0", "3")):
        market = "sz"
    else:
        raise ProviderFetchError("unsupported_symbol", f"unsupported BaoStock symbol: {symbol}")
    if len(code) != 6 or not code.isdigit():
        raise ProviderFetchError("unsupported_symbol", f"invalid BaoStock symbol: {symbol}")
    return f"{market}.{code}"


def asset_kind(symbol: str, asset_type: str | None = None, group_name: str | None = None) -> str:
    asset = str(asset_type or "").upper()
    group = str(group_name or "").upper()
    code = _code(symbol)
    if asset == "ETF" or code.startswith(ETF_PREFIXES):
        return "ETF"
    if asset == "INDEX" or group == "INDEX" or symbol in INDEX_SYMBOLS:
        return "INDEX"
    return "A_STOCK"


def _baostock_module() -> Any:
    try:
        import baostock as bs  # type: ignore
    except Exception as exc:  # pragma: no cover - import environment dependent
        raise ProviderFetchError("import_error", str(exc)) from exc
    return bs


def _akshare_module() -> Any:
    try:
        import akshare as ak  # type: ignore
    except Exception as exc:  # pragma: no cover - import environment dependent
        raise ProviderFetchError("import_error", str(exc)) from exc
    return ak


def _call_stock_em(ak: Any, query_symbol: str, start_date: str, end_date: str) -> Any:
    return ak.stock_zh_a_hist(
        symbol=query_symbol,
        period="daily",
        start_date=start_date,
        end_date=end_date,
        adjust="qfq",
    )


def _call_stock_tx(ak: Any, query_symbol: str, start_date: str, end_date: str) -> Any:
    return ak.stock_zh_a_hist_tx(
        symbol=query_symbol,
        start_date=start_date,
        end_date=end_date,
        adjust="qfq",
    )


def _call_index_tx(ak: Any, query_symbol: str, start_date: str, end_date: str) -> Any:
    return ak.stock_zh_index_daily_tx(symbol=query_symbol)


def _call_index_sina(ak: Any, query_symbol: str, start_date: str, end_date: str) -> Any:
    try:
        return ak.stock_zh_index_daily(symbol=query_symbol)
    except Exception:
        return ak.stock_zh_index_daily(symbol=query_symbol[2:])


def _call_etf_em(ak: Any, query_symbol: str, start_date: str, end_date: str) -> Any:
    return ak.fund_etf_hist_em(
        symbol=query_symbol,
        period="daily",
        start_date=start_date,
        end_date=end_date,
        adjust="qfq",
    )


def _call_fund_nav_em(ak: Any, query_symbol: str, start_date: str, end_date: str) -> Any:
    return ak.fund_open_fund_info_em(symbol=query_symbol, indicator="单位净值走势")


def _call_baostock_daily(bs: Any, query_symbol: str, start_date: str, end_date: str) -> Any:
    login = bs.login()
    if getattr(login, "error_code", "0") != "0":
        raise ProviderFetchError(
            "auth_error",
            getattr(login, "error_msg", "BaoStock login failed"),
        )
    fields = ",".join(
        [
            "date",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "amount",
            "turn",
            "pctChg",
            "peTTM",
            "pbMRQ",
            "psTTM",
            "pcfNcfTTM",
            "tradestatus",
            "isST",
        ]
    )
    try:
        result = bs.query_history_k_data_plus(
            query_symbol,
            fields,
            start_date=f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}",
            end_date=f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}",
            frequency="d",
            adjustflag="2",
        )
        if getattr(result, "error_code", "0") != "0":
            raise ProviderFetchError(
                "remote_error",
                getattr(result, "error_msg", "BaoStock query failed"),
            )
        rows: list[list[str]] = []
        while result.next():
            rows.append(result.get_row_data())
        return pd.DataFrame(rows, columns=list(result.fields))
    finally:
        try:
            bs.logout()
        except Exception:
            pass


PROVIDERS: tuple[ProviderSpec, ...] = (
    ProviderSpec(
        "baostock",
        "query_history_k_data_plus",
        ("A_STOCK",),
        to_baostock_symbol,
        _call_baostock_daily,
    ),
    ProviderSpec("tencent", "stock_zh_a_hist_tx", ("A_STOCK",), to_tx_symbol, _call_stock_tx),
    ProviderSpec("eastmoney", "stock_zh_a_hist", ("A_STOCK",), _code, _call_stock_em),
    ProviderSpec("tencent", "stock_zh_index_daily_tx", ("INDEX",), to_tx_symbol, _call_index_tx),
    ProviderSpec("sina", "stock_zh_index_daily", ("INDEX",), to_tx_symbol, _call_index_sina),
    ProviderSpec("eastmoney", "fund_etf_hist_em", ("ETF",), _code, _call_etf_em),
    ProviderSpec("tencent", "stock_zh_a_hist_tx", ("ETF",), to_tx_symbol, _call_stock_tx),
    ProviderSpec("tencent", "stock_zh_index_daily_tx", ("ETF",), to_tx_symbol, _call_index_tx),
)

PROBE_SPECS: tuple[ProviderSpec, ...] = PROVIDERS + (
    ProviderSpec("eastmoney", "fund_open_fund_info_em", ("FUND",), _code, _call_fund_nav_em),
)


def _classify_error(exc: BaseException) -> tuple[str, str]:
    if isinstance(exc, ProviderFetchError):
        return exc.category, exc.message
    name = exc.__class__.__name__
    text = str(exc)
    lower = f"{name} {text}".lower()
    if "timeout" in lower or "timed out" in lower:
        return "timeout", text or name
    if "remote disconnected" in lower or "connection aborted" in lower:
        return "remote_disconnected", text or name
    if "429" in lower or "rate" in lower or "too many" in lower:
        return "rate_limited", text or name
    if isinstance(exc, KeyError | ValueError | TypeError):
        return "schema_error", text or name
    return "unknown_error", text or name


def _provider_child(
    queue: Queue,
    spec: ProviderSpec,
    query_symbol: str,
    start_date: str,
    end_date: str,
) -> None:
    try:
        module = _baostock_module() if spec.provider == "baostock" else _akshare_module()
        queue.put(("ok", spec.call(module, query_symbol, start_date, end_date)))
    except Exception as exc:
        category, message = _classify_error(exc)
        queue.put(("err", category, message))


def _invoke_with_timeout(
    spec: ProviderSpec,
    query_symbol: str,
    start_date: str,
    end_date: str,
    timeout_seconds: float,
) -> Any:
    ctx = get_context("fork")
    queue: Queue = ctx.Queue(maxsize=1)
    process = ctx.Process(
        target=_provider_child,
        args=(queue, spec, query_symbol, start_date, end_date),
    )
    process.daemon = True
    process.start()
    process.join(timeout_seconds)
    if process.is_alive():
        raise ProviderFetchError("timeout", f"{spec.interface} timed out")
    if queue.empty():
        raise ProviderFetchError("unknown_error", f"{spec.interface} exited without result")
    status, *payload = queue.get()
    if status == "ok":
        return payload[0]
    category, message = payload
    raise ProviderFetchError(str(category), str(message))


def _normalize_raw_daily_bar(
    raw: Any,
    *,
    symbol: str,
    name: str,
    provider: str,
    interface: str,
    fallback_reason: str | None,
) -> tuple[pd.DataFrame, list[str], list[str]]:
    if raw is None:
        raise ProviderFetchError("empty_response", "provider returned None")
    df = pd.DataFrame(raw).copy()
    if df.empty:
        raise ProviderFetchError("empty_response", "provider returned empty dataframe")

    rename_map = {
        "日期": "trade_date",
        "时间": "trade_date",
        "date": "trade_date",
        "day": "trade_date",
        "trade_date": "trade_date",
        "开盘": "open",
        "今开": "open",
        "open": "open",
        "收盘": "close",
        "最新价": "close",
        "close": "close",
        "最高": "high",
        "high": "high",
        "最低": "low",
        "low": "low",
        "成交量": "volume",
        "volume": "volume",
        "成交额": "amount",
        "amount": "amount",
        "turn": "turnover_rate",
        "pctChg": "pct_chg",
        "peTTM": "pe_ttm",
        "pbMRQ": "pb_mrq",
        "psTTM": "ps_ttm",
        "pcfNcfTTM": "pcf_ncf_ttm",
        "tradestatus": "trade_status",
        "isST": "is_st",
    }
    df = df.rename(columns={key: value for key, value in rename_map.items() if key in df.columns})
    required = ["trade_date", "open", "high", "low", "close"]
    missing_required = [col for col in required if col not in df.columns]
    if missing_required:
        raise ProviderFetchError(
            "schema_error",
            f"missing required columns: {', '.join(missing_required)}",
        )

    missing_fields: list[str] = []
    derived_fields: list[str] = []
    optional_fields = (
        "volume",
        "amount",
        "turnover_rate",
        "pct_chg",
        "pe_ttm",
        "pb_mrq",
        "ps_ttm",
        "pcf_ncf_ttm",
        "trade_status",
        "is_st",
    )
    for optional in optional_fields:
        if optional not in df.columns:
            df[optional] = pd.NA
            missing_fields.append(optional)
        elif df[optional].replace("", pd.NA).isna().all():
            missing_fields.append(optional)

    base_columns = ["trade_date", "open", "high", "low", "close", "volume", "amount"]
    result = df[[*base_columns, *optional_fields[2:]]].copy()
    result["trade_date"] = pd.to_datetime(result["trade_date"], errors="coerce").dt.date.astype(str)
    numeric_columns = [
        "open",
        "high",
        "low",
        "close",
        "volume",
        "amount",
        "turnover_rate",
        "pct_chg",
        "pe_ttm",
        "pb_mrq",
        "ps_ttm",
        "pcf_ncf_ttm",
    ]
    for col in numeric_columns:
        result[col] = pd.to_numeric(result[col], errors="coerce")
    result = result.dropna(subset=["trade_date", "open", "high", "low", "close"])
    if result.empty:
        raise ProviderFetchError("empty_response", "no valid OHLC rows after normalization")
    result["symbol"] = symbol
    result["name"] = name
    result["source"] = provider
    result["source_mode"] = "REAL"
    result["source_provider"] = provider
    result["source_interface"] = interface
    result["missing_fields"] = ",".join(sorted(missing_fields))
    result["derived_fields"] = ",".join(sorted(derived_fields))
    result["fallback_reason"] = fallback_reason
    return result[STANDARD_DAILY_BAR_COLUMNS].copy(), missing_fields, derived_fields


def fetch_daily_bar(
    symbol: str,
    name: str,
    asset_type: str | None,
    group_name: str | None,
    start_date: str,
    end_date: str,
    runtime: ProviderRuntime | None = None,
) -> ProviderResult | None:
    runtime = runtime or ProviderRuntime()
    kind = asset_kind(symbol, asset_type, group_name)
    attempts: list[ProviderAttempt] = []
    failed: list[str] = []
    for spec in [item for item in PROVIDERS if kind in item.asset_kinds]:
        if spec.provider in runtime.disabled:
            attempts.append(
                ProviderAttempt(
                    provider=spec.provider,
                    interface=spec.interface,
                    status="skipped",
                    elapsed_ms=0,
                    error_class="provider_disabled",
                    error_message="provider disabled in current sync round",
                )
            )
            continue
        try:
            query_symbol = spec.query_symbol(symbol)
        except Exception as exc:
            category, message = _classify_error(exc)
            attempt = ProviderAttempt(
                provider=spec.provider,
                interface=spec.interface,
                status="failed",
                elapsed_ms=0,
                error_class=category,
                error_message=message[:240],
            )
            attempts.append(attempt)
            runtime.record_failure(spec.provider, category)
            failed.append(f"{spec.provider}.{spec.interface}:{category}")
            continue
        last_error: ProviderAttempt | None = None
        for _ in range(max(1, runtime.retries + 1)):
            started = time.monotonic()
            try:
                raw = _invoke_with_timeout(
                    spec,
                    query_symbol,
                    start_date,
                    end_date,
                    runtime.timeout_seconds,
                )
                fallback_reason = "; ".join(failed) if failed else None
                frame, missing_fields, derived_fields = _normalize_raw_daily_bar(
                    raw,
                    symbol=symbol,
                    name=name,
                    provider=spec.provider,
                    interface=spec.interface,
                    fallback_reason=fallback_reason,
                )
                elapsed = int((time.monotonic() - started) * 1000)
                latest = str(frame["trade_date"].max()) if not frame.empty else None
                attempts.append(
                    ProviderAttempt(
                        provider=spec.provider,
                        interface=spec.interface,
                        status="ok",
                        rows=len(frame),
                        latest_date=latest,
                        elapsed_ms=elapsed,
                    )
                )
                runtime.record_success(spec.provider)
                return ProviderResult(
                    frame=frame,
                    provider=spec.provider,
                    interface=spec.interface,
                    missing_fields=missing_fields,
                    derived_fields=derived_fields,
                    fallback_reason=fallback_reason,
                    attempts=attempts,
                )
            except Exception as exc:
                elapsed = int((time.monotonic() - started) * 1000)
                category, message = _classify_error(exc)
                last_error = ProviderAttempt(
                    provider=spec.provider,
                    interface=spec.interface,
                    status="failed",
                    elapsed_ms=elapsed,
                    error_class=category,
                    error_message=message[:240],
                )
                attempts.append(last_error)
                runtime.record_failure(spec.provider, category)
                if category in {"schema_error", "empty_response", "import_error"}:
                    break
        if last_error:
            failed.append(f"{spec.provider}.{spec.interface}:{last_error.error_class}")
    return None if not attempts else ProviderResult(
        frame=pd.DataFrame(),
        provider="missing",
        interface="missing",
        missing_fields=[],
        derived_fields=[],
        fallback_reason="; ".join(failed) if failed else None,
        attempts=attempts,
    )


def probe_provider(
    spec: ProviderSpec,
    symbol: str,
    start_date: str,
    end_date: str,
    timeout_seconds: float,
) -> ProviderAttempt:
    started = time.monotonic()
    try:
        query_symbol = spec.query_symbol(symbol)
        raw = _invoke_with_timeout(spec, query_symbol, start_date, end_date, timeout_seconds)
        if raw is None:
            raise ProviderFetchError("empty_response", "provider returned None")
        df = pd.DataFrame(raw)
        latest = None
        if not df.empty:
            date_candidates = ("日期", "净值日期", "date", "day", "trade_date")
            date_col = next((col for col in date_candidates if col in df.columns), None)
            if date_col:
                latest = str(pd.to_datetime(df[date_col], errors="coerce").max())[:10]
        return ProviderAttempt(
            provider=spec.provider,
            interface=spec.interface,
            status="ok" if not df.empty else "empty",
            rows=len(df),
            latest_date=latest,
            elapsed_ms=int((time.monotonic() - started) * 1000),
        )
    except Exception as exc:
        category, message = _classify_error(exc)
        return ProviderAttempt(
            provider=spec.provider,
            interface=spec.interface,
            status="failed",
            error_class=category,
            error_message=message[:240],
            elapsed_ms=int((time.monotonic() - started) * 1000),
        )


def specs_for_symbol(symbol: str, asset_type: str | None = None) -> list[ProviderSpec]:
    kind = asset_kind(symbol, asset_type, "INDEX" if symbol in INDEX_SYMBOLS else None)
    return [item for item in PROBE_SPECS if kind in item.asset_kinds]


def provider_attempts_to_json(attempts: list[ProviderAttempt]) -> str:
    return json.dumps([item.to_dict() for item in attempts], ensure_ascii=False)
