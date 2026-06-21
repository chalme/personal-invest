from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import pandas as pd

from worker.storage import (
    RAW_DIR,
    connect_db,
    get_watchlist,
    now_iso,
    read_parquet_dataset,
    write_json_atomic,
    write_partitioned_parquet,
)

INDEX_SYMBOLS = [
    {"symbol": "000001.SH", "name": "上证指数", "group_name": "INDEX"},
    {"symbol": "399001.SZ", "name": "深证成指", "group_name": "INDEX"},
    {"symbol": "399006.SZ", "name": "创业板指", "group_name": "INDEX"},
    {"symbol": "000300.SH", "name": "沪深300", "group_name": "INDEX"},
    {"symbol": "000905.SH", "name": "中证500", "group_name": "INDEX"},
]


NON_REAL_SOURCE_VALUES = {
    "sample",
    "estimated",
    "built_in_sample",
    "deterministic_estimate",
    "instrument_estimate",
    "mock",
    "demo",
}

NON_RECORD_SOURCE_KEYS = {"missing", "unknown", "none", "null"}


def _business_dates(days: int = 180) -> list[date]:
    current = date.today()
    result: list[date] = []
    while len(result) < days:
        if current.weekday() < 5:
            result.append(current)
        current -= timedelta(days=1)
    return list(reversed(result))


def _expected_latest_trade_date(today: date | None = None) -> date:
    current = today or date.today()
    while current.weekday() >= 5:
        current -= timedelta(days=1)
    return current


def _business_day_gap(latest: date, expected: date) -> int:
    if latest >= expected:
        return 0
    days = 0
    current = latest + timedelta(days=1)
    while current <= expected:
        if current.weekday() < 5:
            days += 1
        current += timedelta(days=1)
    return days


def _parse_iso_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _freshness_fields(source_mode: str, latest_data_date: str | None) -> dict[str, Any]:
    expected = _expected_latest_trade_date()
    latest = _parse_iso_date(latest_data_date)
    if source_mode == "MISSING" or latest is None:
        status = "MISSING"
        stale_days: int | None = None
    elif latest >= expected:
        status = "FRESH"
        stale_days = 0
    else:
        status = "STALE"
        stale_days = _business_day_gap(latest, expected)
    return {
        "expected_latest_trade_date": expected.isoformat(),
        "trade_calendar_source_mode": "ESTIMATED",
        "freshness_status": status,
        "stale_days": stale_days,
        "can_drive_advice": source_mode == "REAL" and status == "FRESH",
    }


def _freshness_warning(
    dataset_label: str, freshness: dict[str, Any], latest_data_date: str | None
) -> str | None:
    calendar_note = "最近交易日按工作日估算，未纳入法定节假日或临时休市。"
    status = freshness.get("freshness_status")
    if status == "FRESH":
        return calendar_note
    if status == "STALE":
        return (
            f"{dataset_label}最新日期 {latest_data_date or '暂无'}，落后预期最近交易日 "
            f"{freshness.get('expected_latest_trade_date')} "
            f"约 {freshness.get('stale_days')} 个交易日；"
            f"{calendar_note}"
        )
    if status == "MISSING":
        return f"{dataset_label}缺少可判断新鲜度的数据日期；{calendar_note}"
    return None


def _source_mode_from_count(source_count: dict[str, int]) -> str:
    sample_count = sum(
        int(value or 0)
        for key, value in source_count.items()
        if key.lower() in NON_REAL_SOURCE_VALUES
    )
    real_count = sum(
        int(value or 0)
        for key, value in source_count.items()
        if key.lower() not in NON_REAL_SOURCE_VALUES | NON_RECORD_SOURCE_KEYS
    )
    if real_count > 0 and sample_count > 0:
        return "MIXED"
    if real_count > 0:
        return "REAL"
    if sample_count > 0:
        return "SAMPLE"
    return "MISSING"


def _source_warning(dataset_label: str, source_mode: str) -> str | None:
    if source_mode == "REAL":
        return None
    if source_mode == "MIXED":
        return f"{dataset_label}包含真实数据和历史非真实数据，非真实部分不可用于投资判断。"
    if source_mode == "SAMPLE":
        return f"{dataset_label}来自历史样本或估算数据，属于待清理污染，不可作为正常运行数据。"
    return f"{dataset_label}缺失或来源不明确，请检查数据同步任务。"


def _build_manifest(
    *,
    dataset: str,
    generated_at: str,
    rows: int,
    assets: list[str],
    latest_data_date: str | None,
    source_count: dict[str, int],
    asset_key: str,
    latest_key: str,
    dataset_label: str,
    extra_warnings: list[str] | None = None,
    can_drive_advice_override: bool | None = None,
    asset_source_status: dict[str, str] | None = None,
) -> dict[str, Any]:
    source_mode = _source_mode_from_count(source_count)
    freshness = _freshness_fields(source_mode, latest_data_date)
    if can_drive_advice_override is not None:
        freshness["can_drive_advice"] = can_drive_advice_override
    warnings = []
    for warning in (
        _source_warning(dataset_label, source_mode),
        _freshness_warning(dataset_label, freshness, latest_data_date),
    ):
        if warning:
            warnings.append(warning)
    warnings.extend(extra_warnings or [])
    manifest = {
        "dataset": dataset,
        "generated_at": generated_at,
        "latest_data_date": latest_data_date,
        "rows": rows,
        "asset_count": len(assets),
        "source_count": source_count,
        "source_mode": source_mode,
        "warning": " ".join(warnings) if warnings else None,
        **freshness,
        "asset_source_status": asset_source_status or {},
        asset_key: assets,
        latest_key: latest_data_date,
    }
    return manifest


def _code(symbol: str) -> str:
    return symbol.split(".")[0]


def _fetch_with_akshare(
    symbol: str, name: str, start_date: str, end_date: str
) -> pd.DataFrame | None:
    try:
        import akshare as ak  # type: ignore
    except Exception:
        return None

    code = _code(symbol)
    try:
        if code.startswith(("51", "15", "16")):
            raw = ak.fund_etf_hist_em(
                symbol=code, period="daily", start_date=start_date, end_date=end_date, adjust="qfq"
            )
        elif symbol in {"000001.SH", "399001.SZ", "399006.SZ", "000300.SH", "000905.SH"}:
            raw = ak.stock_zh_index_daily(symbol=code)
        else:
            raw = ak.stock_zh_a_hist(
                symbol=code, period="daily", start_date=start_date, end_date=end_date, adjust="qfq"
            )
    except Exception:
        return None

    if raw is None or raw.empty:
        return None
    rename_map = {
        "日期": "trade_date",
        "开盘": "open",
        "收盘": "close",
        "最高": "high",
        "最低": "low",
        "成交量": "volume",
        "成交额": "amount",
        "date": "trade_date",
        "open": "open",
        "close": "close",
        "high": "high",
        "low": "low",
        "volume": "volume",
        "amount": "amount",
    }
    df = raw.rename(columns={k: v for k, v in rename_map.items() if k in raw.columns})
    required = ["trade_date", "open", "high", "low", "close"]
    if any(col not in df.columns for col in required):
        return None
    if "volume" not in df.columns:
        df["volume"] = 0
    if "amount" not in df.columns:
        df["amount"] = df["close"].astype(float) * df["volume"].astype(float)
    df = df[["trade_date", "open", "high", "low", "close", "volume", "amount"]].copy()
    df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date.astype(str)
    df["symbol"] = symbol
    df["name"] = name
    df["source"] = "akshare"
    return df


def _historical_real_bars(
    symbol: str,
    name: str,
    history: pd.DataFrame,
    max_days: int,
) -> pd.DataFrame | None:
    if history.empty or "symbol" not in history.columns or "trade_date" not in history.columns:
        return None
    frame = history[history["symbol"].astype(str) == symbol].copy()
    if frame.empty:
        return None
    if "source" in frame.columns:
        frame = frame[~frame["source"].astype(str).str.lower().isin(NON_REAL_SOURCE_VALUES)].copy()
    if frame.empty:
        return None
    required = ["trade_date", "open", "high", "low", "close"]
    if any(col not in frame.columns for col in required):
        return None
    if "volume" not in frame.columns:
        frame["volume"] = 0
    if "amount" not in frame.columns:
        frame["amount"] = frame["close"].astype(float) * frame["volume"].astype(float)
    frame["symbol"] = symbol
    frame["name"] = name
    frame["trade_date"] = pd.to_datetime(frame["trade_date"]).dt.date.astype(str)
    frame["source"] = "akshare_cached"
    columns = [
        "trade_date",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "amount",
        "symbol",
        "name",
        "source",
    ]
    frame = frame[columns].copy()
    return frame.sort_values("trade_date").tail(max_days).reset_index(drop=True)


def sync_market_data(days: int = 180) -> dict[str, Any]:
    with connect_db() as conn:
        symbols = get_watchlist(conn)
    merged: dict[str, dict[str, Any]] = {item["symbol"]: item for item in INDEX_SYMBOLS + symbols}
    business_dates = _business_dates(days)
    start_date = business_dates[0].strftime("%Y%m%d")
    end_date = business_dates[-1].strftime("%Y%m%d")
    historical_daily_bar = read_parquet_dataset("daily_bar")
    frames: list[pd.DataFrame] = []
    source_count = {"akshare": 0, "akshare_cached": 0, "missing": 0}
    asset_source_status: dict[str, str] = {}
    fallback_symbols: list[str] = []
    missing_symbols: list[str] = []
    for item in merged.values():
        symbol = str(item["symbol"])
        name = str(item.get("name") or symbol)
        frame = _fetch_with_akshare(symbol, name, start_date, end_date)
        if frame is None or frame.empty:
            frame = _historical_real_bars(symbol, name, historical_daily_bar, days)
            if frame is None or frame.empty:
                source_count["missing"] += 1
                asset_source_status[symbol] = "missing"
                missing_symbols.append(symbol)
                continue
            else:
                source_count["akshare_cached"] += 1
                asset_source_status[symbol] = "akshare_cached"
                fallback_symbols.append(symbol)
        else:
            source_count["akshare"] += 1
            asset_source_status[symbol] = "akshare"
        frames.append(frame)
    generated_at = now_iso()
    requested_assets = sorted(str(item["symbol"]) for item in merged.values())
    missing_warning = (
        f"{len(missing_symbols)} 个资产缺少 AKShare 数据且没有可复用真实历史，"
        "已标记为 MISSING，未生成样本行情。"
        if missing_symbols
        else None
    )
    fallback_warning = (
        f"{len(fallback_symbols)} 个资产 AKShare 同步失败，"
        "已保留最近成功真实历史；相关资产不应驱动高置信当日价格建议。"
        if fallback_symbols
        else None
    )
    if not frames:
        manifest = _build_manifest(
            dataset="daily_bar",
            generated_at=generated_at,
            rows=0,
            assets=requested_assets,
            latest_data_date=None,
            source_count=source_count,
            asset_key="symbols",
            latest_key="latest_trade_date",
            dataset_label="行情日线",
            extra_warnings=[warning for warning in (missing_warning, fallback_warning) if warning],
            can_drive_advice_override=False,
            asset_source_status=asset_source_status,
        )
        write_json_atomic(
            RAW_DIR / "market" / f"{date.today().isoformat()}_manifest.json", manifest
        )
        return {**manifest, "status": "missing", "dataset": "daily_bar"}

    df = pd.concat(frames, ignore_index=True)
    df["data_version"] = f"daily_bar_{df['trade_date'].max()}_{now_iso()}"
    df = df.sort_values(["trade_date", "symbol"]).reset_index(drop=True)
    assets = requested_assets
    latest_data_date = str(df["trade_date"].max())
    manifest = _build_manifest(
        dataset="daily_bar",
        generated_at=generated_at,
        rows=len(df),
        assets=assets,
        latest_data_date=latest_data_date,
        source_count=source_count,
        asset_key="symbols",
        latest_key="latest_trade_date",
        dataset_label="行情日线",
        extra_warnings=[warning for warning in (missing_warning, fallback_warning) if warning],
        can_drive_advice_override=False if fallback_symbols or missing_symbols else None,
        asset_source_status=asset_source_status,
    )
    write_json_atomic(RAW_DIR / "market" / f"{date.today().isoformat()}_manifest.json", manifest)
    target = write_partitioned_parquet(df, "daily_bar", ["trade_date"])
    return {**manifest, "status": "ok", "dataset": str(target)}


def _fetch_fund_nav_with_akshare(symbol: str, name: str) -> pd.DataFrame | None:
    try:
        import akshare as ak  # type: ignore
    except Exception:
        return None
    try:
        raw = ak.fund_open_fund_info_em(symbol=_code(symbol), indicator="单位净值走势")
    except Exception:
        return None
    if raw is None or raw.empty:
        return None
    rename_map = {"净值日期": "nav_date", "单位净值": "nav", "date": "nav_date", "value": "nav"}
    df = raw.rename(columns={key: value for key, value in rename_map.items() if key in raw.columns})
    if "nav_date" not in df.columns or "nav" not in df.columns:
        return None
    df = df[["nav_date", "nav"]].copy()
    df["nav_date"] = pd.to_datetime(df["nav_date"]).dt.date.astype(str)
    df["nav"] = pd.to_numeric(df["nav"], errors="coerce")
    df = df.dropna(subset=["nav"])
    if df.empty:
        return None
    df["symbol"] = symbol
    df["name"] = name
    df["source"] = "akshare"
    return df


def _historical_real_nav(
    symbol: str,
    name: str,
    history: pd.DataFrame,
    max_days: int,
) -> pd.DataFrame | None:
    if history.empty or "symbol" not in history.columns or "nav_date" not in history.columns:
        return None
    frame = history[history["symbol"].astype(str) == symbol].copy()
    if frame.empty:
        return None
    if "source" in frame.columns:
        frame = frame[~frame["source"].astype(str).str.lower().isin(NON_REAL_SOURCE_VALUES)].copy()
    if frame.empty or "nav" not in frame.columns:
        return None
    if "accumulated_nav" not in frame.columns:
        frame["accumulated_nav"] = frame["nav"]
    frame["symbol"] = symbol
    frame["name"] = name
    frame["nav_date"] = pd.to_datetime(frame["nav_date"]).dt.date.astype(str)
    frame["nav"] = pd.to_numeric(frame["nav"], errors="coerce")
    frame["accumulated_nav"] = pd.to_numeric(frame["accumulated_nav"], errors="coerce")
    frame = frame.dropna(subset=["nav"])
    if frame.empty:
        return None
    frame["source"] = "akshare_cached"
    columns = ["nav_date", "nav", "accumulated_nav", "symbol", "name", "source"]
    frame = frame[columns].copy()
    return frame.sort_values("nav_date").tail(max_days).reset_index(drop=True)


def sync_fund_data(days: int = 180) -> dict[str, Any]:
    with connect_db() as conn:
        watchlist = get_watchlist(conn)
    funds = [item for item in watchlist if str(item.get("asset_type") or "").upper() == "FUND"]
    if not funds:
        manifest = _build_manifest(
            dataset="fund_nav",
            generated_at=now_iso(),
            rows=0,
            assets=[],
            latest_data_date=None,
            source_count={"akshare": 0, "akshare_cached": 0, "missing": 0},
            asset_key="funds",
            latest_key="latest_nav_date",
            dataset_label="基金净值",
        )
        write_json_atomic(RAW_DIR / "fund" / f"{date.today().isoformat()}_manifest.json", manifest)
        return {**manifest, "status": "skipped", "dataset": "fund_nav"}

    historical_fund_nav = read_parquet_dataset("fund_nav")
    frames: list[pd.DataFrame] = []
    source_count = {"akshare": 0, "akshare_cached": 0, "missing": 0}
    fund_source_status: dict[str, str] = {}
    fallback_funds: list[str] = []
    missing_funds: list[str] = []
    for item in funds:
        symbol = str(item["symbol"])
        name = str(item.get("name") or symbol)
        frame = _fetch_fund_nav_with_akshare(symbol, name)
        if frame is None or frame.empty:
            frame = _historical_real_nav(symbol, name, historical_fund_nav, days)
            if frame is None or frame.empty:
                source_count["missing"] += 1
                fund_source_status[symbol] = "missing"
                missing_funds.append(symbol)
                continue
            else:
                source_count["akshare_cached"] += 1
                fund_source_status[symbol] = "akshare_cached"
                fallback_funds.append(symbol)
        else:
            source_count["akshare"] += 1
            fund_source_status[symbol] = "akshare"
        frames.append(frame)

    generated_at = now_iso()
    requested_assets = sorted(str(item["symbol"]) for item in funds)
    missing_warning = (
        f"{len(missing_funds)} 只基金缺少 AKShare 净值且没有可复用真实历史，"
        "已标记为 MISSING，未生成样本净值。"
        if missing_funds
        else None
    )
    fallback_warning = (
        f"{len(fallback_funds)} 只基金 AKShare 净值同步失败，"
        "已保留最近成功真实净值；相关基金不应驱动高置信当日基金建议。"
        if fallback_funds
        else None
    )
    if not frames:
        manifest = _build_manifest(
            dataset="fund_nav",
            generated_at=generated_at,
            rows=0,
            assets=requested_assets,
            latest_data_date=None,
            source_count=source_count,
            asset_key="funds",
            latest_key="latest_nav_date",
            dataset_label="基金净值",
            extra_warnings=[warning for warning in (missing_warning, fallback_warning) if warning],
            can_drive_advice_override=False,
            asset_source_status=fund_source_status,
        )
        write_json_atomic(RAW_DIR / "fund" / f"{date.today().isoformat()}_manifest.json", manifest)
        return {**manifest, "status": "missing", "dataset": "fund_nav"}

    df = pd.concat(frames, ignore_index=True)
    df["data_version"] = f"fund_nav_{df['nav_date'].max()}_{now_iso()}"
    df = df.sort_values(["nav_date", "symbol"]).reset_index(drop=True)
    assets = requested_assets
    latest_data_date = str(df["nav_date"].max())
    manifest = _build_manifest(
        dataset="fund_nav",
        generated_at=generated_at,
        rows=len(df),
        assets=assets,
        latest_data_date=latest_data_date,
        source_count=source_count,
        asset_key="funds",
        latest_key="latest_nav_date",
        dataset_label="基金净值",
        extra_warnings=[warning for warning in (missing_warning, fallback_warning) if warning],
        can_drive_advice_override=False if fallback_funds or missing_funds else None,
        asset_source_status=fund_source_status,
    )
    write_json_atomic(RAW_DIR / "fund" / f"{date.today().isoformat()}_manifest.json", manifest)
    target = write_partitioned_parquet(df, "fund_nav", ["nav_date"])
    return {**manifest, "status": "ok", "dataset": str(target)}
