from __future__ import annotations

import json
from typing import Any

from worker.storage import connect_db, now_iso, upsert_many

RULE_CODE = "personal_advice_v1"
RULE_VERSION = "1.0.0"
STRATEGY_CODE = "personal_watch_v1"


def infer_asset_type(symbol: str) -> str:
    code = symbol.upper().split(".")[0]
    suffix = symbol.upper().split(".")[-1] if "." in symbol else ""
    if suffix in {"OF", "FUND"}:
        return "FUND"
    if code.startswith(("15", "16", "50", "51", "52", "56", "58")):
        return "ETF"
    return "STOCK"

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
    with connect_db() as conn:
        previous_rows = conn.execute(
            """
            SELECT symbol, advice_level
            FROM investment_advice
            WHERE account_id = ?
              AND advice_date = (
                  SELECT MAX(advice_date)
                  FROM investment_advice
                  WHERE account_id = ? AND advice_date < ?
              )
            """,
            (account_id, account_id, advice_date),
        ).fetchall()
    previous_by_symbol = {row["symbol"]: row["advice_level"] for row in previous_rows}
    assets: dict[str, dict[str, Any]] = {}
    for row in watchlist:
        assets[row["symbol"]] = dict(row)
    for row in positions:
        assets.setdefault(row["symbol"], dict(row))

    values: list[tuple[Any, ...]] = []
    for symbol, asset in assets.items():
        asset_type = str(asset.get("asset_type") or infer_asset_type(symbol)).upper()
        position = position_by_symbol.get(symbol)
        if asset_type != "STOCK":
            analysis = fund_by_symbol.get(symbol)
            if not analysis:
                continue
            advice = _fund_advice(analysis, position)
            data_version = analysis.get("data_version") or latest_fund_date
            source_snapshot_type = analysis.get("analysis_type") or "FUND_NAV"
            source_snapshot_date = latest_fund_date
            name = analysis.get("name") or asset.get("name") or symbol
        else:
            analysis = stock_by_symbol.get(symbol)
            if not analysis:
                continue
            advice = _stock_advice(analysis, position, market_score)
            data_version = analysis.get("data_version") or latest_stock_date
            source_snapshot_type = "STOCK_ANALYSIS"
            source_snapshot_date = latest_stock_date
            name = analysis.get("name") or asset.get("name") or symbol
        previous_level = previous_by_symbol.get(symbol)
        change_reason = "首次生成建议" if not previous_level else ("建议等级未变化" if previous_level == advice["level"] else f"建议由{previous_level}调整为{advice['level']}")
        rule_result = {
            "rule_code": RULE_CODE,
            "rule_version": RULE_VERSION,
            "strategy_code": STRATEGY_CODE,
            "source_snapshot_type": source_snapshot_type,
            "source_snapshot_date": source_snapshot_date,
            "matched_level": advice["level"],
            "metrics": advice["key_metrics"],
        }
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
            RULE_CODE,
            RULE_VERSION,
            STRATEGY_CODE,
            source_snapshot_type,
            source_snapshot_date,
            previous_level,
            change_reason,
            json.dumps(rule_result, ensure_ascii=False),
        ))

    with connect_db() as conn:
        count = upsert_many(conn, """
            INSERT INTO investment_advice(
                account_id, symbol, name, asset_type, holding_status, advice_date,
                advice_level, one_liner, trigger_reason, key_metrics, risk_note,
                review_action, confidence, data_version, created_at, rule_code, rule_version,
                strategy_code, source_snapshot_type, source_snapshot_date, previous_advice_level,
                change_reason, rule_result
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                created_at = excluded.created_at,
                rule_code = excluded.rule_code,
                rule_version = excluded.rule_version,
                strategy_code = excluded.strategy_code,
                source_snapshot_type = excluded.source_snapshot_type,
                source_snapshot_date = excluded.source_snapshot_date,
                previous_advice_level = excluded.previous_advice_level,
                change_reason = excluded.change_reason,
                rule_result = excluded.rule_result
        """, values)
    return {"count": count, "advice_date": advice_date}
