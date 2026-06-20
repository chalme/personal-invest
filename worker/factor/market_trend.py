from __future__ import annotations

from typing import Any

import pandas as pd

from worker.storage import connect_db, now_iso, read_parquet_dataset, upsert_many, write_partitioned_parquet


def classify_market(score: float) -> str:
    if score >= 80:
        return "强势"
    if score >= 60:
        return "偏强"
    if score >= 40:
        return "震荡"
    if score >= 20:
        return "偏弱"
    return "高风险"


def _score_ratio(value: float, low: float, high: float) -> float:
    if high == low:
        return 50.0
    return max(0.0, min(100.0, (value - low) / (high - low) * 100))


def _latest_symbol_features(df: pd.DataFrame) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for symbol, group in df.sort_values("trade_date").groupby("symbol"):
        g = group.copy()
        g["ma20"] = g["close"].rolling(20, min_periods=5).mean()
        g["ma60"] = g["close"].rolling(60, min_periods=20).mean()
        g["ma120"] = g["close"].rolling(120, min_periods=40).mean()
        g["momentum_20"] = g["close"].pct_change(20)
        g["momentum_60"] = g["close"].pct_change(60)
        g["amount_ma20"] = g["amount"].rolling(20, min_periods=5).mean()
        g["volume_change"] = g["amount"] / g["amount_ma20"] - 1
        g["symbol"] = symbol
        frames.append(g.tail(1))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def calculate_market_trend() -> dict[str, Any]:
    df = read_parquet_dataset("daily_bar")
    if df.empty:
        raise RuntimeError("daily_bar Parquet 不存在，请先同步行情数据")
    df = df.copy()
    df["trade_date"] = df["trade_date"].astype(str)
    latest_date = str(df["trade_date"].max())
    latest = _latest_symbol_features(df)
    index_df = latest[latest["symbol"].isin(["000001.SH", "399001.SZ", "399006.SZ", "000300.SH", "000905.SH"])]
    above_ma20 = float((latest["close"] > latest["ma20"]).mean())
    above_ma60 = float((latest["close"] > latest["ma60"]).mean())
    momentum_20 = float(latest["momentum_20"].fillna(0).mean())
    momentum_60 = float(latest["momentum_60"].fillna(0).mean())
    volume_change = float(latest["volume_change"].replace([float("inf"), -float("inf")], 0).fillna(0).mean())

    if not index_df.empty:
        index_score = (
            45
            + float((index_df["close"] > index_df["ma20"]).mean()) * 18
            + float((index_df["close"] > index_df["ma60"]).mean()) * 18
            + max(-20, min(20, float(index_df["momentum_20"].fillna(0).mean()) * 300))
        )
    else:
        index_score = 50
    breadth_score = above_ma20 * 55 + above_ma60 * 35 + _score_ratio(momentum_20, -0.08, 0.12) * 0.10
    volume_score = _score_ratio(volume_change, -0.30, 0.50)
    sector_score = _score_ratio(momentum_60, -0.12, 0.20)
    sentiment_score = _score_ratio(momentum_20, -0.08, 0.12)
    fund_flow_score = volume_score * 0.6 + sentiment_score * 0.4
    market_score = round(max(0, min(100, index_score * 0.30 + breadth_score * 0.25 + volume_score * 0.15 + sector_score * 0.15 + sentiment_score * 0.10 + fund_flow_score * 0.05)), 2)
    state = classify_market(market_score)
    summary = f"市场{state}，MA20 上方比例 {above_ma20:.0%}，20日动量 {momentum_20:.2%}，量能变化 {volume_change:.2%}。"
    now = now_iso()
    with connect_db() as conn:
        for table in [
            "market_trend_snapshot",
            "sector_trend_snapshot",
            "stock_analysis_snapshot",
            "strategy_signal",
            "risk_event",
        ]:
            conn.execute(f"DELETE FROM {table} WHERE trade_date > ?", (latest_date,))
        conn.execute("DELETE FROM report_index WHERE report_type = 'daily' AND report_date > ?", (latest_date,))
        conn.execute(
            """
            INSERT INTO market_trend_snapshot(
                trade_date, market_score, trend_state, index_trend_score, breadth_score,
                volume_score, sector_score, sentiment_score, fund_flow_score, summary, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(trade_date) DO UPDATE SET
                market_score = excluded.market_score,
                trend_state = excluded.trend_state,
                index_trend_score = excluded.index_trend_score,
                breadth_score = excluded.breadth_score,
                volume_score = excluded.volume_score,
                sector_score = excluded.sector_score,
                sentiment_score = excluded.sentiment_score,
                fund_flow_score = excluded.fund_flow_score,
                summary = excluded.summary,
                created_at = excluded.created_at
            """,
            (latest_date, market_score, state, round(index_score, 2), round(breadth_score, 2), round(volume_score, 2), round(sector_score, 2), round(sentiment_score, 2), round(fund_flow_score, 2), summary, now),
        )
        conn.commit()
    factor = latest[["symbol", "name", "trade_date", "close", "ma20", "ma60", "ma120", "momentum_20", "momentum_60", "volume_change"]].copy()
    factor["factor_name"] = "market_trend_features"
    factor["data_version"] = f"market_factor_{latest_date}_{now}"
    write_partitioned_parquet(factor, "market_breadth", ["trade_date"])
    return {"trade_date": latest_date, "market_score": market_score, "trend_state": state, "summary": summary}


def calculate_sector_trend() -> dict[str, Any]:
    df = read_parquet_dataset("daily_bar")
    if df.empty:
        raise RuntimeError("daily_bar Parquet 不存在，请先同步行情数据")
    with connect_db() as conn:
        watchlist = conn.execute("SELECT symbol, group_name FROM watchlist WHERE status = 'ACTIVE'").fetchall()
    sector_map = {row["symbol"]: row["group_name"] or "未分组" for row in watchlist}
    rows: list[dict[str, Any]] = []
    for symbol, group in df.sort_values("trade_date").groupby("symbol"):
        if symbol not in sector_map:
            continue
        latest = group.tail(1).iloc[0]
        close = group["close"]
        momentum_20 = close.iloc[-1] / close.iloc[-21] - 1 if len(close) > 21 else 0
        momentum_60 = close.iloc[-1] / close.iloc[-61] - 1 if len(close) > 61 else momentum_20
        amount_ma20 = group["amount"].tail(20).mean() if len(group) >= 5 else group["amount"].mean()
        volume_change = latest["amount"] / amount_ma20 - 1 if amount_ma20 else 0
        rows.append({"trade_date": str(latest["trade_date"]), "sector_code": str(sector_map[symbol]).upper().replace(" ", "_"), "sector_name": str(sector_map[symbol]), "momentum_20": float(momentum_20), "momentum_60": float(momentum_60), "volume_change": float(volume_change)})
    if not rows:
        return {"count": 0}
    sector_df = pd.DataFrame(rows).groupby(["trade_date", "sector_code", "sector_name"], as_index=False).mean(numeric_only=True)
    sector_df["trend_score"] = (50 + sector_df["momentum_20"].clip(-0.15, 0.20) * 180 + sector_df["momentum_60"].clip(-0.25, 0.35) * 80 + sector_df["volume_change"].clip(-0.40, 0.80) * 20).clip(0, 100).round(2)
    sector_df = sector_df.sort_values("trend_score", ascending=False).reset_index(drop=True)
    sector_df["rank"] = sector_df.index + 1
    sector_df["state"] = sector_df["trend_score"].apply(classify_market)
    sector_df["strength_reason"] = sector_df.apply(lambda r: f"20日动量 {r['momentum_20']:.2%}，60日动量 {r['momentum_60']:.2%}，量能 {r['volume_change']:.2%}", axis=1)
    sector_df["risk_note"] = sector_df["trend_score"].apply(lambda s: "短期过热，注意回撤" if s >= 80 else "趋势仍需持续验证")
    values = [(r.trade_date, r.sector_code, r.sector_name, float(r.trend_score), int(r.rank), r.state, float(r.momentum_20), float(r.momentum_60), float(r.volume_change), r.strength_reason, r.risk_note) for r in sector_df.itertuples(index=False)]
    with connect_db() as conn:
        count = upsert_many(conn, """
            INSERT INTO sector_trend_snapshot(
                trade_date, sector_code, sector_name, trend_score, rank, state,
                momentum_20, momentum_60, volume_change, strength_reason, risk_note
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(trade_date, sector_code) DO UPDATE SET
                sector_name = excluded.sector_name,
                trend_score = excluded.trend_score,
                rank = excluded.rank,
                state = excluded.state,
                momentum_20 = excluded.momentum_20,
                momentum_60 = excluded.momentum_60,
                volume_change = excluded.volume_change,
                strength_reason = excluded.strength_reason,
                risk_note = excluded.risk_note
            """, values)
    write_partitioned_parquet(sector_df, "sector_factor", ["trade_date"])
    return {"count": count, "latest_trade_date": str(sector_df["trade_date"].max())}
