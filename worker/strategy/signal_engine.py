from __future__ import annotations

import json
from typing import Any

from worker.storage import connect_db, now_iso, upsert_many


DEFAULT_STRATEGY_PARAMS: dict[str, float] = {
    "high_quality_score": 80,
    "high_quality_market_score": 45,
    "trend_watch_score": 65,
    "trend_watch_market_score": 55,
    "risk_score": 45,
}


def infer_asset_type(symbol: str) -> str:
    code = symbol.upper().split(".")[0]
    suffix = symbol.upper().split(".")[-1] if "." in symbol else ""
    if suffix in {"OF", "FUND"}:
        return "FUND"
    if code.startswith(("15", "16", "50", "51", "52", "56", "58")):
        return "ETF"
    return "STOCK"


def load_strategy_config(strategy_code: str = "personal_watch_v1") -> dict[str, Any]:
    params = dict(DEFAULT_STRATEGY_PARAMS)
    enabled = True
    strategy_name = "个人观察策略 V1"
    with connect_db() as conn:
        row = conn.execute(
            """
            SELECT strategy_name, enabled, config_json
            FROM strategy_config
            WHERE strategy_code = ?
            """,
            (strategy_code,),
        ).fetchone()
    if not row:
        return {"strategy_code": strategy_code, "strategy_name": strategy_name, "enabled": enabled, "params": params}
    enabled = bool(row["enabled"])
    strategy_name = row["strategy_name"] or strategy_name
    try:
        raw_params = json.loads(row["config_json"] or "{}")
    except json.JSONDecodeError:
        raw_params = {}
    for key, default in DEFAULT_STRATEGY_PARAMS.items():
        try:
            value = float(raw_params.get(key, default))
        except (TypeError, ValueError):
            value = default
        params[key] = min(100.0, max(0.0, value))
    return {"strategy_code": strategy_code, "strategy_name": strategy_name, "enabled": enabled, "params": params}


def generate_signals() -> dict[str, Any]:
    config = load_strategy_config()
    strategy_code = config["strategy_code"]
    params = config["params"]
    now = now_iso()
    with connect_db() as conn:
        market = conn.execute("SELECT * FROM market_trend_snapshot ORDER BY trade_date DESC LIMIT 1").fetchone()
        stocks = conn.execute(
            """
            SELECT * FROM stock_analysis_snapshot
            WHERE trade_date = (SELECT MAX(trade_date) FROM stock_analysis_snapshot)
            ORDER BY total_score DESC
            """
        ).fetchall()
        funds = conn.execute(
            """
            SELECT * FROM fund_analysis_snapshot
            WHERE nav_date = (SELECT MAX(nav_date) FROM fund_analysis_snapshot)
            ORDER BY total_score DESC
            """
        ).fetchall()
    if not market:
        return {"count": 0, "strategy_code": strategy_code, "enabled": config["enabled"]}
    trade_date = market["trade_date"]
    if not config["enabled"]:
        return {"count": 0, "trade_date": trade_date, "strategy_code": strategy_code, "enabled": False}

    market_score = float(market["market_score"])
    values: list[tuple[Any, ...]] = []
    for row in stocks:
        score = float(row["total_score"])
        if score >= params["high_quality_score"] and market_score >= params["high_quality_market_score"]:
            signal_type = "高质量观察"
            risk_level = "LOW"
            reason = f"综合评分 {score:.0f}，市场评分 {market_score:.0f}，达到高质量观察阈值。"
        elif score >= params["trend_watch_score"] and market_score >= params["trend_watch_market_score"]:
            signal_type = "趋势观察"
            risk_level = "MEDIUM"
            reason = f"综合评分 {score:.0f}，市场评分 {market_score:.0f}，达到趋势观察阈值。"
        elif score < params["risk_score"]:
            signal_type = "风险上升"
            risk_level = "HIGH"
            reason = f"综合评分降至 {score:.0f}，低于风险阈值 {params['risk_score']:.0f}。"
        else:
            continue
        values.append((strategy_code, row["symbol"], row["name"], infer_asset_type(row["symbol"]), trade_date, signal_type, score, reason, risk_level, row["data_version"], now))

    for row in funds:
        score = float(row["total_score"])
        if score >= params["trend_watch_score"]:
            signal_type = "基金稳健观察"
            risk_level = "MEDIUM"
            reason = f"基金综合评分 {score:.0f}，趋势评分 {float(row['trend_score'] or 0):.0f}，风险评分 {float(row['risk_score'] or 0):.0f}。"
        elif score < params["risk_score"]:
            signal_type = "基金风险上升"
            risk_level = "HIGH"
            reason = f"基金综合评分降至 {score:.0f}，低于风险阈值 {params['risk_score']:.0f}，需关注回撤和波动。"
        else:
            continue
        values.append((strategy_code, row["symbol"], row["name"], "FUND", trade_date, signal_type, score, reason, risk_level, row["data_version"], now))
    with connect_db() as conn:
        count = upsert_many(conn, """
            INSERT INTO strategy_signal(
                strategy_code, symbol, name, asset_type, trade_date, signal_type, score, reason, risk_level, data_version, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(strategy_code, symbol, trade_date) DO UPDATE SET
                name = excluded.name,
                asset_type = excluded.asset_type,
                signal_type = excluded.signal_type,
                score = excluded.score,
                reason = excluded.reason,
                risk_level = excluded.risk_level,
                data_version = excluded.data_version,
                created_at = excluded.created_at
            """, values)
    return {"count": count, "trade_date": trade_date, "strategy_code": strategy_code, "enabled": True}


def _confidence(score: float, holding: bool) -> float:
    base = 0.55 + min(abs(score - 60) / 120, 0.3)
    if holding:
        base += 0.08
    return round(min(base, 0.95), 2)


def _stock_advice(row: dict[str, Any], position: dict[str, Any] | None, market_score: float) -> dict[str, Any]:
    score = float(row.get("total_score") or 0)
    pnl_ratio = float(position.get("pnl_ratio") or 0) if position else 0.0
    position_ratio = float(position.get("position_ratio") or 0) if position else 0.0
    holding = position is not None
    name = row.get("name") or (position or {}).get("name") or row["symbol"]
    metrics = {
        "total_score": round(score, 2),
        "market_score": round(market_score, 2),
        "trend_score": row.get("trend_score"),
        "risk_score": row.get("risk_score"),
        "pnl_ratio": round(pnl_ratio, 4),
        "position_ratio": round(position_ratio, 4),
    }
    if holding:
        if score < 45 or pnl_ratio <= -0.08:
            level = "卖出关注"
            one_liner = f"{name} 评分或盈亏触发风险线，今天需要复核是否退出。"
            review_action = "检查是否跌破止损价、评分是否连续下滑，并决定是否降低或清空仓位。"
        elif score < 60 or position_ratio >= 0.35 or pnl_ratio >= 0.2:
            level = "减仓关注"
            one_liner = f"{name} 当前更适合控制仓位，先确认收益兑现或风险暴露。"
            review_action = "复核仓位占比、上涨后的回撤空间和继续持有理由。"
        elif score >= 65:
            level = "持有"
            one_liner = f"{name} 评分仍支持持有，但需要跟踪趋势和风险边界。"
            review_action = "继续跟踪评分、行业强弱和止损/止盈观察价。"
        else:
            level = "继续观察"
            one_liner = f"{name} 没有明确加减仓信号，维持观察。"
            review_action = "等待评分、趋势或基本面出现更明确变化。"
    else:
        if score >= 80 and market_score >= 55:
            level = "买入关注"
            one_liner = f"{name} 质量和市场环境同时较好，可以进入买入候选复核。"
            review_action = "复核估值、买入区间和单笔仓位上限，确认后再人工操作。"
        elif score >= 65:
            level = "继续观察"
            one_liner = f"{name} 评分较好，但还未同时满足买入关注条件。"
            review_action = "继续观察趋势确认、估值安全边际和市场评分变化。"
        elif score < 45:
            level = "卖出关注"
            one_liner = f"{name} 评分偏弱，不适合作为新的买入候选。"
            review_action = "复核是否应从观察池降级，避免弱势标的占用注意力。"
        else:
            level = "继续观察"
            one_liner = f"{name} 当前信号不足，先保留观察。"
            review_action = "等待评分或行业趋势出现明确改善。"
    return {
        "level": level,
        "one_liner": one_liner,
        "trigger_reason": f"综合评分 {score:.0f}，市场评分 {market_score:.0f}，当前盈亏 {pnl_ratio:.2%}，仓位 {position_ratio:.2%}。",
        "key_metrics": metrics,
        "risk_note": row.get("risk_note") or "暂无额外风险说明。",
        "review_action": review_action,
        "confidence": _confidence(score, holding),
    }


def _fund_advice(row: dict[str, Any], position: dict[str, Any] | None) -> dict[str, Any]:
    score = float(row.get("total_score") or 0)
    risk_score = float(row.get("risk_score") or 0)
    drawdown = float(row.get("max_drawdown") or 0)
    pnl_ratio = float(position.get("pnl_ratio") or 0) if position else 0.0
    position_ratio = float(position.get("position_ratio") or 0) if position else 0.0
    holding = position is not None
    name = row.get("name") or (position or {}).get("name") or row["symbol"]
    metrics = {
        "total_score": round(score, 2),
        "risk_score": round(risk_score, 2),
        "return_3m": row.get("return_3m"),
        "max_drawdown": round(drawdown, 4),
        "volatility": row.get("volatility"),
        "pnl_ratio": round(pnl_ratio, 4),
        "position_ratio": round(position_ratio, 4),
    }
    if holding:
        if score < 45 or risk_score < 45 or drawdown <= -0.12:
            level = "卖出关注"
            one_liner = f"{name} 回撤或风险评分偏弱，需要复核是否赎回或降低暴露。"
            review_action = "检查最大回撤、近三月收益和组合占比，决定是否分批降低基金仓位。"
        elif score < 60 or position_ratio >= 0.35:
            level = "减仓关注"
            one_liner = f"{name} 当前基金风险收益比一般，优先控制仓位。"
            review_action = "复核基金风格、波动和同类替代品，避免单基金过度集中。"
        elif score >= 65:
            level = "持有"
            one_liner = f"{name} 基金评分支持继续持有，重点跟踪回撤边界。"
            review_action = "继续跟踪净值趋势、回撤和基金在组合中的占比。"
        else:
            level = "继续观察"
            one_liner = f"{name} 暂无明确调仓信号，维持观察。"
            review_action = "等待收益、回撤或趋势评分出现更明确变化。"
    else:
        if score >= 70 and risk_score >= 60:
            level = "买入关注"
            one_liner = f"{name} 风险收益评分较好，可以进入基金买入候选复核。"
            review_action = "复核基金类型、申赎规则、费率和组合配置比例，再人工确认。"
        elif score < 45:
            level = "卖出关注"
            one_liner = f"{name} 基金评分偏弱，不适合作为新增候选。"
            review_action = "复核是否从观察池降级，等待回撤和趋势改善。"
        else:
            level = "继续观察"
            one_liner = f"{name} 需要继续观察净值趋势和回撤。"
            review_action = "跟踪近三月收益、最大回撤和风险评分。"
    return {
        "level": level,
        "one_liner": one_liner,
        "trigger_reason": f"基金评分 {score:.0f}，风险评分 {risk_score:.0f}，最大回撤 {drawdown:.2%}，当前盈亏 {pnl_ratio:.2%}。",
        "key_metrics": metrics,
        "risk_note": row.get("risk_note") or "暂无额外风险说明。",
        "review_action": review_action,
        "confidence": _confidence(score, holding),
    }


def generate_investment_advice(account_id: int = 1) -> dict[str, Any]:
    now = now_iso()
    with connect_db() as conn:
        market = conn.execute("SELECT * FROM market_trend_snapshot ORDER BY trade_date DESC LIMIT 1").fetchone()
        latest_stock_date = conn.execute("SELECT MAX(trade_date) AS trade_date FROM stock_analysis_snapshot").fetchone()["trade_date"]
        latest_fund_date = conn.execute("SELECT MAX(nav_date) AS nav_date FROM fund_analysis_snapshot").fetchone()["nav_date"]
        stock_rows = conn.execute("SELECT * FROM stock_analysis_snapshot WHERE trade_date = ?", (latest_stock_date,)).fetchall() if latest_stock_date else []
        fund_rows = conn.execute("SELECT * FROM fund_analysis_snapshot WHERE nav_date = ?", (latest_fund_date,)).fetchall() if latest_fund_date else []
        positions = conn.execute("SELECT * FROM portfolio_position WHERE account_id = ?", (account_id,)).fetchall()
        watchlist = conn.execute("SELECT * FROM watchlist WHERE status = 'ACTIVE'").fetchall()
    if not market:
        return {"count": 0, "advice_date": None}

    advice_date = market["trade_date"]
    market_score = float(market["market_score"] or 0)
    stock_by_symbol = {row["symbol"]: dict(row) for row in stock_rows}
    fund_by_symbol = {row["symbol"]: dict(row) for row in fund_rows}
    position_by_symbol = {row["symbol"]: dict(row) for row in positions}
    assets: dict[str, dict[str, Any]] = {}
    for row in watchlist:
        assets[row["symbol"]] = dict(row)
    for row in positions:
        assets.setdefault(row["symbol"], dict(row))

    values: list[tuple[Any, ...]] = []
    for symbol, asset in assets.items():
        asset_type = str(asset.get("asset_type") or infer_asset_type(symbol)).upper()
        position = position_by_symbol.get(symbol)
        if asset_type == "FUND":
            analysis = fund_by_symbol.get(symbol)
            if not analysis:
                continue
            advice = _fund_advice(analysis, position)
            data_version = analysis.get("data_version") or latest_fund_date
            name = analysis.get("name") or asset.get("name") or symbol
        else:
            analysis = stock_by_symbol.get(symbol)
            if not analysis:
                continue
            advice = _stock_advice(analysis, position, market_score)
            data_version = analysis.get("data_version") or latest_stock_date
            name = analysis.get("name") or asset.get("name") or symbol
        values.append((
            account_id,
            symbol,
            name,
            asset_type,
            "HOLDING" if position else "WATCHING",
            advice_date,
            advice["level"],
            advice["one_liner"],
            advice["trigger_reason"],
            json.dumps(advice["key_metrics"], ensure_ascii=False),
            advice["risk_note"],
            advice["review_action"],
            advice["confidence"],
            data_version,
            now,
        ))

    with connect_db() as conn:
        count = upsert_many(conn, """
            INSERT INTO investment_advice(
                account_id, symbol, name, asset_type, holding_status, advice_date,
                advice_level, one_liner, trigger_reason, key_metrics, risk_note,
                review_action, confidence, data_version, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(account_id, symbol, advice_date) DO UPDATE SET
                name = excluded.name,
                asset_type = excluded.asset_type,
                holding_status = excluded.holding_status,
                advice_level = excluded.advice_level,
                one_liner = excluded.one_liner,
                trigger_reason = excluded.trigger_reason,
                key_metrics = excluded.key_metrics,
                risk_note = excluded.risk_note,
                review_action = excluded.review_action,
                confidence = excluded.confidence,
                data_version = excluded.data_version,
                created_at = excluded.created_at
        """, values)
    return {"count": count, "advice_date": advice_date}
