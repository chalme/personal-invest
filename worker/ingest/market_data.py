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
    manifest = {
        "generated_at": now_iso(),
        "rows": len(df),
        "symbols": sorted(df["symbol"].unique().tolist()),
        "latest_trade_date": str(df["trade_date"].max()),
        "source_count": source_count,
    }
    write_json_atomic(RAW_DIR / "market" / f"{date.today().isoformat()}_manifest.json", manifest)
    target = write_partitioned_parquet(df, "daily_bar", ["trade_date"])
    return {**manifest, "status": "ok", "dataset": str(target)}
