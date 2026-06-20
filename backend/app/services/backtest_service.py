from __future__ import annotations

import math
from typing import Any

import duckdb
import pandas as pd

from app.core.config import get_settings
from app.repositories.sqlite_repo import SQLiteRepository


class BacktestService:
    def __init__(self, repo: SQLiteRepository | None = None) -> None:
        self.repo = repo or SQLiteRepository()
        self.settings = get_settings()

    def watchlist_equal_weight(self, initial_cash: float = 100000.0, limit: int = 500) -> dict[str, Any]:
        initial_cash = max(float(initial_cash or 100000), 1000.0)
        limit = max(30, min(int(limit or 500), 2000))
        watchlist = self.repo.fetch_all(
            """
            SELECT symbol, name
            FROM watchlist
            WHERE status = 'ACTIVE'
            ORDER BY priority DESC, symbol ASC
            """
        )
        symbols = [item["symbol"] for item in watchlist]
        if not symbols:
            return self._empty("NO_WATCHLIST", "暂无自选股，无法回测。")

        parquet_glob = self._daily_bar_glob()
        if parquet_glob is None:
            return self._empty("NO_DATA", "暂无行情 Parquet 数据，请先执行每日更新。")

        prices = self._load_prices(parquet_glob, symbols)
        if prices.empty:
            return self._empty("NO_PRICE", "自选股缺少可用行情数据。")

        result = self._calculate(prices, symbols, initial_cash, limit)
        result["holdings"] = [
            {"symbol": item["symbol"], "name": item.get("name") or item["symbol"]}
            for item in watchlist
            if item["symbol"] in result["summary"]["used_symbols"]
        ]
        return result

    def _daily_bar_glob(self) -> str | None:
        base = self.settings.data_dir / "parquet" / "daily_bar"
        if not base.exists() or not any(base.rglob("*.parquet")):
            return None
        return str(base / "**" / "*.parquet")

    def _load_prices(self, parquet_glob: str, symbols: list[str]) -> pd.DataFrame:
        placeholders = ",".join(["?"] * len(symbols))
        sql = f"""
            SELECT
                CAST(trade_date AS VARCHAR) AS trade_date,
                symbol,
                close
            FROM read_parquet(?, hive_partitioning = true)
            WHERE symbol IN ({placeholders})
            ORDER BY trade_date ASC, symbol ASC
        """
        with duckdb.connect(database=":memory:", read_only=False) as conn:
            df = conn.execute(sql, [parquet_glob, *symbols]).fetchdf()
        if df.empty:
            return df
        df["trade_date"] = pd.to_datetime(df["trade_date"], errors="coerce").dt.date.astype(str)
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        return df.dropna(subset=["trade_date", "symbol", "close"])

    def _calculate(self, prices: pd.DataFrame, requested_symbols: list[str], initial_cash: float, limit: int) -> dict[str, Any]:
        pivot = prices.pivot_table(index="trade_date", columns="symbol", values="close", aggfunc="last").sort_index()
        pivot = pivot.loc[:, [symbol for symbol in requested_symbols if symbol in pivot.columns]]
        pivot = pivot.dropna(axis=1, how="all")
        if pivot.shape[0] < 2 or pivot.shape[1] == 0:
            return self._empty("INSUFFICIENT_DATA", "可用交易日不足，无法计算回测指标。")

        returns = pivot.pct_change().replace([math.inf, -math.inf], pd.NA).dropna(how="all")
        used_symbols = [symbol for symbol in pivot.columns if returns[symbol].notna().any()]
        if returns.empty or not used_symbols:
            return self._empty("INSUFFICIENT_RETURN", "无法计算有效收益率序列。")

        portfolio_return = returns[used_symbols].mean(axis=1, skipna=True).fillna(0.0)
        equity = initial_cash * (1.0 + portfolio_return).cumprod()
        peak = equity.cummax()
        drawdown = (equity / peak) - 1.0

        benchmark_symbol = used_symbols[0]
        benchmark_return = returns[benchmark_symbol].fillna(0.0)
        benchmark_equity = initial_cash * (1.0 + benchmark_return).cumprod()

        trading_days = int(len(portfolio_return))
        total_return = float(equity.iloc[-1] / initial_cash - 1.0)
        annualized_return = self._annualize(total_return, trading_days)
        volatility = float(portfolio_return.std(ddof=0) * math.sqrt(252)) if trading_days > 1 else 0.0
        sharpe = annualized_return / volatility if volatility > 0 else None
        win_rate = float((portfolio_return > 0).mean()) if trading_days else 0.0
        max_drawdown = float(drawdown.min()) if not drawdown.empty else 0.0
        benchmark_total_return = float(benchmark_equity.iloc[-1] / initial_cash - 1.0)

        curve_index = list(equity.index)[-limit:]
        curve = [
            {
                "trade_date": str(date),
                "equity": round(float(equity.loc[date]), 2),
                "benchmark_equity": round(float(benchmark_equity.loc[date]), 2),
                "daily_return": round(float(portfolio_return.loc[date]), 6),
                "drawdown": round(float(drawdown.loc[date]), 6),
            }
            for date in curve_index
        ]

        return {
            "backtest_id": "watchlist_equal_weight_v1",
            "name": "自选股等权回测",
            "status": "OK",
            "summary": {
                "start_date": str(equity.index[0]),
                "end_date": str(equity.index[-1]),
                "initial_cash": round(initial_cash, 2),
                "final_equity": round(float(equity.iloc[-1]), 2),
                "total_return": round(total_return, 6),
                "annualized_return": round(annualized_return, 6),
                "max_drawdown": round(max_drawdown, 6),
                "win_rate": round(win_rate, 6),
                "volatility": round(volatility, 6),
                "sharpe_ratio": round(float(sharpe), 6) if sharpe is not None else None,
                "benchmark_symbol": benchmark_symbol,
                "benchmark_return": round(benchmark_total_return, 6),
                "trading_days": trading_days,
                "used_symbols": used_symbols,
            },
            "curve": curve,
            "holdings": [],
            "notes": [
                "当前回测为自选股等权持有模型，不代表真实交易建议。",
                "该版本暂不模拟手续费、滑点、停牌、涨跌停和调仓约束。",
                "后续可扩展为基于策略信号的事件驱动回测。",
            ],
        }

    def _annualize(self, total_return: float, trading_days: int) -> float:
        if trading_days <= 0:
            return 0.0
        if total_return <= -1:
            return -1.0
        return float((1.0 + total_return) ** (252.0 / trading_days) - 1.0)

    def _empty(self, status: str, message: str) -> dict[str, Any]:
        return {
            "backtest_id": "watchlist_equal_weight_v1",
            "name": "自选股等权回测",
            "status": status,
            "summary": {},
            "curve": [],
            "holdings": [],
            "notes": [message],
        }
