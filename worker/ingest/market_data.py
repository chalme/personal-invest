from __future__ import annotations

import hashlib
import math
from datetime import date, timedelta
from typing import Any

import pandas as pd

from worker.storage import RAW_DIR, connect_db, get_watchlist, now_iso, write_json_atomic, write_partitioned_parquet

INDEX_SYMBOLS = [
    {"symbol": "000001.SH", "name": "上证指数", "group_name": "INDEX"},
    {"symbol": "399001.SZ", "name": "深证成指", "group_name": "INDEX"},
    {"symbol": "399006.SZ", "name": "创业板指", "group_name": "INDEX"},
    {"symbol": "000300.SH", "name": "沪深300", "group_name": "INDEX"},
    {"symbol": "000905.SH", "name": "中证500", "group_name": "INDEX"},
]


def _stable_seed(text: str) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16)


def _business_dates(days: int = 180) -> list[date]:
    current = date.today()
    result: list[date] = []
    while len(result) < days:
        if current.weekday() < 5:
            result.append(current)
        current -= timedelta(days=1)
    return list(reversed(result))



def _source_mode_from_count(source_count: dict[str, int]) -> str:
    sample_count = int(source_count.get("sample") or 0)
    real_count = sum(int(value or 0) for key, value in source_count.items() if key.lower() != "sample")
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
        return f"{dataset_label}包含真实数据和样本数据，分析结论需要结合数据来源谨慎使用。"
    if source_mode == "SAMPLE":
        return f"{dataset_label}全部来自样本数据，仅用于功能演示，不应作为真实投资依据。"
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
) -> dict[str, Any]:
    source_mode = _source_mode_from_count(source_count)
    manifest = {
        "dataset": dataset,
        "generated_at": generated_at,
        "latest_data_date": latest_data_date,
        "rows": rows,
        "asset_count": len(assets),
        "source_count": source_count,
        "source_mode": source_mode,
        "warning": _source_warning(dataset_label, source_mode),
        asset_key: assets,
        latest_key: latest_data_date,
    }
    return manifest

def _code(symbol: str) -> str:
    return symbol.split(".")[0]


def _fetch_with_akshare(symbol: str, name: str, start_date: str, end_date: str) -> pd.DataFrame | None:
    try:
        import akshare as ak  # type: ignore
    except Exception:
        return None

    code = _code(symbol)
    try:
        if code.startswith(("51", "15", "16")):
            raw = ak.fund_etf_hist_em(symbol=code, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
        elif symbol in {"000001.SH", "399001.SZ", "399006.SZ", "000300.SH", "000905.SH"}:
            raw = ak.stock_zh_index_daily(symbol=code)
        else:
            raw = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
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


def _generate_sample_bars(symbol: str, name: str, days: list[date]) -> pd.DataFrame:
    seed = _stable_seed(symbol)
    base = 8 + seed % 90
    if symbol in {"000001.SH", "399001.SZ", "399006.SZ", "000300.SH", "000905.SH"}:
        base = 2800 + seed % 900
    if symbol.startswith("510"):
        base = 3 + (seed % 200) / 100
    trend = ((seed % 9) - 3) / 1000
    rows: list[dict[str, Any]] = []
    prev_close = float(base)
    for i, d in enumerate(days):
        wave = math.sin(i / 7 + seed % 11) * 0.012
        drift = trend + math.sin(i / 31) * 0.0015
        close = max(0.5, prev_close * (1 + drift + wave))
        open_price = prev_close * (1 + math.sin(i / 5 + seed % 7) * 0.004)
        high = max(open_price, close) * (1 + 0.006 + (seed % 5) * 0.001)
        low = min(open_price, close) * (1 - 0.006 - (seed % 3) * 0.001)
        volume = 900_000 + (seed % 500_000) + i * 1200
        amount = close * volume * (100 if close < 100 else 1)
        rows.append({
            "symbol": symbol,
            "name": name,
            "trade_date": d.isoformat(),
            "open": round(open_price, 4),
            "high": round(high, 4),
            "low": round(low, 4),
            "close": round(close, 4),
            "volume": float(volume),
            "amount": round(float(amount), 2),
            "source": "sample",
        })
        prev_close = close
    return pd.DataFrame(rows)


def sync_market_data(days: int = 180) -> dict[str, Any]:
    with connect_db() as conn:
        symbols = get_watchlist(conn)
    merged: dict[str, dict[str, Any]] = {item["symbol"]: item for item in INDEX_SYMBOLS + symbols}
    business_dates = _business_dates(days)
    start_date = business_dates[0].strftime("%Y%m%d")
    end_date = business_dates[-1].strftime("%Y%m%d")
    frames: list[pd.DataFrame] = []
    source_count = {"akshare": 0, "sample": 0}
    for item in merged.values():
        symbol = str(item["symbol"])
        name = str(item.get("name") or symbol)
        frame = _fetch_with_akshare(symbol, name, start_date, end_date)
        if frame is None or frame.empty:
            frame = _generate_sample_bars(symbol, name, business_dates)
            source_count["sample"] += 1
        else:
            source_count["akshare"] += 1
        frames.append(frame)
    df = pd.concat(frames, ignore_index=True)
    df["data_version"] = f"daily_bar_{df['trade_date'].max()}_{now_iso()}"
    df = df.sort_values(["trade_date", "symbol"]).reset_index(drop=True)
    generated_at = now_iso()
    assets = sorted(df["symbol"].unique().tolist())
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


def _generate_sample_nav(symbol: str, name: str, days: list[date]) -> pd.DataFrame:
    seed = _stable_seed(symbol)
    base = 0.8 + (seed % 120) / 100
    trend = ((seed % 7) - 2) / 1500
    rows: list[dict[str, Any]] = []
    prev_nav = float(base)
    for i, current in enumerate(days):
        wave = math.sin(i / 11 + seed % 13) * 0.006
        nav = max(0.2, prev_nav * (1 + trend + wave))
        rows.append({
            "symbol": symbol,
            "name": name,
            "nav_date": current.isoformat(),
            "nav": round(nav, 4),
            "accumulated_nav": round(nav * (1 + (seed % 9) / 100), 4),
            "source": "sample",
        })
        prev_nav = nav
    return pd.DataFrame(rows)


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
            source_count={"akshare": 0, "sample": 0},
            asset_key="funds",
            latest_key="latest_nav_date",
            dataset_label="基金净值",
        )
        write_json_atomic(RAW_DIR / "fund" / f"{date.today().isoformat()}_manifest.json", manifest)
        return {**manifest, "status": "skipped", "dataset": "fund_nav"}

    business_dates = _business_dates(days)
    frames: list[pd.DataFrame] = []
    source_count = {"akshare": 0, "sample": 0}
    for item in funds:
        symbol = str(item["symbol"])
        name = str(item.get("name") or symbol)
        frame = _fetch_fund_nav_with_akshare(symbol, name)
        if frame is None or frame.empty:
            frame = _generate_sample_nav(symbol, name, business_dates)
            source_count["sample"] += 1
        else:
            source_count["akshare"] += 1
        frames.append(frame)

    df = pd.concat(frames, ignore_index=True)
    df["data_version"] = f"fund_nav_{df['nav_date'].max()}_{now_iso()}"
    df = df.sort_values(["nav_date", "symbol"]).reset_index(drop=True)
    generated_at = now_iso()
    assets = sorted(df["symbol"].unique().tolist())
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
    )
    write_json_atomic(RAW_DIR / "fund" / f"{date.today().isoformat()}_manifest.json", manifest)
    target = write_partitioned_parquet(df, "fund_nav", ["nav_date"])
    return {**manifest, "status": "ok", "dataset": str(target)}
