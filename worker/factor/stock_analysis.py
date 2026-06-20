from __future__ import annotations

from typing import Any

import pandas as pd

from worker.storage import connect_db, now_iso, read_parquet_dataset, upsert_many, write_partitioned_parquet

QUALITY_PROFILE = {
    "600519.SH": {"fundamental": 94, "valuation": 62, "risk": 18},
    "510300.SH": {"fundamental": 68, "valuation": 70, "risk": 24},
    "000001.SZ": {"fundamental": 63, "valuation": 72, "risk": 36},
}


def classify_stock(score: float) -> str:
    if score >= 80:
        return "高质量观察"
    if score >= 65:
        return "趋势观察"
    if score >= 50:
        return "持有观察"
    if score >= 35:
        return "风险上升"
    return "暂不关注"


def _score_trend(row: pd.Series) -> float:
    score = 50.0
    close = float(row["close"])
    for col, weight in [("ma20", 12), ("ma60", 12), ("ma120", 8)]:
        value = row.get(col)
        if pd.notna(value) and close > float(value):
            score += weight
        else:
            score -= weight * 0.6
    score += max(-18, min(18, float(row.get("momentum_20") or 0) * 220))
    score += max(-12, min(12, float(row.get("momentum_60") or 0) * 120))
    score -= max(0, min(12, float(row.get("volatility_20") or 0) * 180))
    return round(max(0, min(100, score)), 2)


def _features(df: pd.DataFrame) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for symbol, group in df.sort_values("trade_date").groupby("symbol"):
        g = group.copy()
        g["ma20"] = g["close"].rolling(20, min_periods=5).mean()
        g["ma60"] = g["close"].rolling(60, min_periods=20).mean()
        g["ma120"] = g["close"].rolling(120, min_periods=40).mean()
        g["momentum_20"] = g["close"].pct_change(20)
        g["momentum_60"] = g["close"].pct_change(60)
        g["return_1"] = g["close"].pct_change()
        g["volatility_20"] = g["return_1"].rolling(20, min_periods=5).std()
        g["amount_ma20"] = g["amount"].rolling(20, min_periods=5).mean()
        g["fund_flow_score"] = ((g["amount"] / g["amount_ma20"] - 1).clip(-0.5, 1.0) * 30 + 55).clip(0, 100)
        g["symbol"] = symbol
        frames.append(g.tail(1))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def calculate_stock_analysis() -> dict[str, Any]:
    df = read_parquet_dataset("daily_bar")
    if df.empty:
        raise RuntimeError("daily_bar Parquet 不存在，请先同步行情数据")
    df = df.copy()
    df["trade_date"] = df["trade_date"].astype(str)
    with connect_db() as conn:
        watchlist = conn.execute(""" SELECT w.symbol, COALESCE(i.name, w.name) AS name, w.group_name, COALESCE(i.asset_type, w.asset_type) AS asset_type FROM watchlist w LEFT JOIN instrument i ON i.symbol = w.symbol WHERE w.status = 'ACTIVE' """).fetchall()
        sector_rows = conn.execute("SELECT sector_name, trend_score FROM sector_trend_snapshot WHERE trade_date = (SELECT MAX(trade_date) FROM sector_trend_snapshot)").fetchall()
    watch = {row["symbol"]: dict(row) for row in watchlist if str(row["asset_type"]).upper() == 'STOCK'}
    sector_scores = {row["sector_name"]: float(row["trend_score"]) for row in sector_rows}
    latest = _features(df)
    latest = latest[latest["symbol"].isin(watch.keys())].copy()
    if latest.empty:
        return {"count": 0}
    now = now_iso()
    latest_date = str(latest["trade_date"].max())
    records: list[tuple[Any, ...]] = []
    factor_rows: list[dict[str, Any]] = []
    for row in latest.itertuples(index=False):
        item = watch[str(row.symbol)]
        profile = QUALITY_PROFILE.get(str(row.symbol), {"fundamental": 60, "valuation": 60, "risk": 35})
        trend_score = _score_trend(pd.Series(row._asdict()))
        fundamental_score = float(profile["fundamental"])
        valuation_score = float(profile["valuation"])
        fund_flow_score = float(getattr(row, "fund_flow_score", 50) or 50)
        sector_score = float(sector_scores.get(item.get("group_name") or "未分组", 55))
        risk_score = float(profile["risk"])
        total_score = round(trend_score * 0.25 + fundamental_score * 0.25 + valuation_score * 0.15 + fund_flow_score * 0.10 + sector_score * 0.10 + (100 - risk_score) * 0.15, 2)
        state = classify_stock(total_score)
        conclusion = f"{item['name']} 当前为{state}，趋势分 {trend_score:.0f}，基本面分 {fundamental_score:.0f}，估值分 {valuation_score:.0f}。"
        risk_note = "趋势偏弱，先观察" if trend_score < 50 else "评分仅作为观察依据，不构成交易指令"
        records.append((latest_date, row.symbol, item["name"], total_score, state, trend_score, fundamental_score, valuation_score, round(fund_flow_score, 2), round(sector_score, 2), risk_score, conclusion, risk_note, f"stock_analysis_{latest_date}_{now}", now))
        factor_rows.append({"trade_date": latest_date, "symbol": row.symbol, "name": item["name"], "close": row.close, "ma20": row.ma20, "ma60": row.ma60, "ma120": row.ma120, "momentum_20": row.momentum_20, "momentum_60": row.momentum_60, "volatility_20": row.volatility_20, "trend_score": trend_score, "total_score": total_score, "data_version": f"stock_factor_{latest_date}_{now}"})
    with connect_db() as conn:
        count = upsert_many(conn, """
            INSERT INTO stock_analysis_snapshot(
                trade_date, symbol, name, total_score, state, trend_score, fundamental_score,
                valuation_score, fund_flow_score, sector_score, risk_score, conclusion,
                risk_note, data_version, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(trade_date, symbol) DO UPDATE SET
                name = excluded.name,
                total_score = excluded.total_score,
                state = excluded.state,
                trend_score = excluded.trend_score,
                fundamental_score = excluded.fundamental_score,
                valuation_score = excluded.valuation_score,
                fund_flow_score = excluded.fund_flow_score,
                sector_score = excluded.sector_score,
                risk_score = excluded.risk_score,
                conclusion = excluded.conclusion,
                risk_note = excluded.risk_note,
                data_version = excluded.data_version,
                created_at = excluded.created_at
            """, records)
    write_partitioned_parquet(pd.DataFrame(factor_rows), "stock_factor", ["trade_date"])
    return {"count": count, "latest_trade_date": latest_date}
