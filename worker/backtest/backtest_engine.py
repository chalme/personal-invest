"""轻量回测模块。

当前实现为自选股等权持有模型。后续事件驱动回测必须保证 T 日信号只能使用
T 日前已经可见的数据。
"""

from __future__ import annotations

import math
from typing import Any

import pandas as pd

from worker.storage import connect_db, read_parquet_dataset


def run_backtest(strategy_code: str = "watchlist_equal_weight_v1") -> dict[str, Any]:
    if strategy_code != "watchlist_equal_weight_v1":
        return {"strategy_code": strategy_code, "status": "unsupported"}

    with connect_db() as conn:
        rows = conn.execute("SELECT symbol FROM watchlist WHERE status = 'ACTIVE' ORDER BY priority DESC, symbol ASC").fetchall()
    symbols = [row["symbol"] for row in rows]
    bars = read_parquet_dataset("daily_bar")
    if not symbols or bars.empty:
        return {"strategy_code": strategy_code, "status": "no_data"}

    bars = bars[bars["symbol"].isin(symbols)].copy()
    bars["trade_date"] = pd.to_datetime(bars["trade_date"], errors="coerce").dt.date.astype(str)
    bars["close"] = pd.to_numeric(bars["close"], errors="coerce")
    pivot = bars.pivot_table(index="trade_date", columns="symbol", values="close", aggfunc="last").sort_index()
    returns = pivot.pct_change().dropna(how="all")
    if returns.empty:
        return {"strategy_code": strategy_code, "status": "insufficient_data"}

    daily_return = returns.mean(axis=1, skipna=True).fillna(0)
    total_return = float((1 + daily_return).prod() - 1)
    max_drawdown = float(((1 + daily_return).cumprod() / (1 + daily_return).cumprod().cummax() - 1).min())
    volatility = float(daily_return.std(ddof=0) * math.sqrt(252)) if len(daily_return) > 1 else 0.0
    return {
        "strategy_code": strategy_code,
        "status": "ok",
        "total_return": round(total_return, 6),
        "max_drawdown": round(max_drawdown, 6),
        "volatility": round(volatility, 6),
        "trading_days": int(len(daily_return)),
        "symbols": list(pivot.columns),
    }

