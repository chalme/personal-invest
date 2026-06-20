from __future__ import annotations

from datetime import datetime

from app.repositories.sqlite_repo import SQLiteRepository


class AIService:
    """Deterministic local analyst.

    This service intentionally does not call an external LLM by default. It turns
    the latest system snapshots into structured explanations, so the AI page is
    useful even before an API key is configured.
    """

    def __init__(self, repo: SQLiteRepository | None = None) -> None:
        self.repo = repo or SQLiteRepository()

    def explain_market(self) -> dict:
        market = self.repo.fetch_one(
            "SELECT * FROM market_trend_snapshot ORDER BY trade_date DESC, id DESC LIMIT 1"
        )
        sectors = self.repo.fetch_all(
            """
            SELECT * FROM sector_trend_snapshot
            WHERE trade_date = (SELECT MAX(trade_date) FROM sector_trend_snapshot)
            ORDER BY rank ASC
            LIMIT 5
            """
        )
        risks = self.repo.fetch_all(
            "SELECT * FROM risk_event ORDER BY trade_date DESC, severity DESC, id DESC LIMIT 5"
        )
        if not market:
            return self._empty_result("market", "暂无市场数据", "请先执行每日更新任务。")

        score = float(market.get("market_score") or 0)
        stance = "积极观察" if score >= 70 else "适度参与" if score >= 55 else "控制仓位" if score >= 40 else "优先防守"
        sector_names = "、".join(item["sector_name"] for item in sectors[:3]) or "暂无"
        risk_notes = [item["message"] for item in risks]

        sections = [
            {"title": "当前市场状态", "content": f"市场处于“{market['trend_state']}”，综合评分 {score:.1f}/100。"},
            {"title": "主要依据", "content": f"指数趋势 {market.get('index_trend_score')}，市场宽度 {market.get('breadth_score')}，量能 {market.get('volume_score')}，行业扩散 {market.get('sector_score')}。"},
            {"title": "强势方向", "content": f"当前排名靠前的行业包括：{sector_names}。"},
            {"title": "风险信号", "content": "；".join(risk_notes) if risk_notes else "暂无高优先级风险事件。"},
            {"title": "仓位含义", "content": f"当前更适合“{stance}”，系统不生成自动交易指令，最终操作需要人工确认。"},
        ]
        return self._record("market", "MARKET", market["trade_date"], sections)

    def explain_portfolio(self) -> dict:
        positions = self.repo.fetch_all("SELECT * FROM portfolio_position ORDER BY position_ratio DESC, market_value DESC")
        risks = self.repo.fetch_all("SELECT * FROM risk_event ORDER BY trade_date DESC, severity DESC, id DESC LIMIT 8")
        advice = self.repo.fetch_all(
            """
            SELECT * FROM investment_advice
            WHERE advice_date = (SELECT MAX(advice_date) FROM investment_advice)
            ORDER BY confidence DESC, id DESC
            LIMIT 8
            """
        )
        if not positions:
            return self._empty_result("portfolio", "暂无持仓数据", "请先录入持仓。")

        total_value = sum(float(item.get("market_value") or 0) for item in positions)
        total_pnl = sum(float(item.get("pnl") or 0) for item in positions)
        top = positions[0]
        risk_count = len(risks)
        sections = [
            {"title": "组合概览", "content": f"当前持仓 {len(positions)} 个，总市值约 {total_value:.2f}，浮动盈亏 {total_pnl:.2f}。"},
            {"title": "集中度", "content": f"最大持仓为 {top.get('name') or top['symbol']}，仓位占比 {float(top.get('position_ratio') or 0) * 100:.2f}%。"},
            {"title": "主要风险", "content": "；".join(item["message"] for item in risks[:5]) if risk_count else "暂无风险事件。"},
            {"title": "规则建议", "content": "；".join(f"{item['name'] or item['symbol']}：{item['advice_level']}，{item['one_liner']}" for item in advice[:5]) if advice else "暂无分级建议，请先执行每日更新。"},
            {"title": "复盘重点", "content": "优先检查大仓位、亏损扩大、跌破止损位、评分下降以及建议等级变化的持仓。"},
            {"title": "操作边界", "content": "AI 只解释规则生成的建议，不直接替你下单；最终买卖需要人工确认。"},
        ]
        latest_date = risks[0]["trade_date"] if risks else datetime.now().date().isoformat()
        return self._record("portfolio", "PORTFOLIO", latest_date, sections)

    def explain_stock(self, symbol: str) -> dict:
        stock = self.repo.fetch_one(
            """
            SELECT * FROM stock_analysis_snapshot
            WHERE symbol = ?
            ORDER BY trade_date DESC, id DESC
            LIMIT 1
            """,
            (symbol,),
        )
        if not stock:
            return self._empty_result("stock", symbol, "暂无该股票分析数据，请先加入自选股并执行每日更新。")

        sections = [
            {"title": "综合结论", "content": f"{stock['name']} 当前状态为“{stock['state']}”，综合评分 {float(stock['total_score']):.1f}/100。"},
            {"title": "趋势面", "content": f"趋势评分 {stock.get('trend_score')}，用于衡量价格动量和均线结构。"},
            {"title": "基本面与估值", "content": f"基本面评分 {stock.get('fundamental_score')}，估值评分 {stock.get('valuation_score')}。"},
            {"title": "资金与行业", "content": f"资金评分 {stock.get('fund_flow_score')}，行业评分 {stock.get('sector_score')}。"},
            {"title": "风险点", "content": str(stock.get('risk_note') or "暂无风险说明。")},
            {"title": "操作边界", "content": "该结论用于观察和复盘，不构成自动交易指令。"},
        ]
        return self._record("stock", symbol, stock["trade_date"], sections)

    def explain_fund(self, symbol: str) -> dict:
        fund = self.repo.fetch_one(
            """
            SELECT * FROM fund_analysis_snapshot
            WHERE symbol = ?
            ORDER BY nav_date DESC, id DESC
            LIMIT 1
            """,
            (symbol,),
        )
        if not fund:
            return self._empty_result("fund", symbol, "暂无该基金分析数据，请先加入观察池并执行每日更新。")

        sections = [
            {"title": "综合结论", "content": f"{fund['name']} 当前状态为“{fund['state']}”，综合评分 {float(fund['total_score']):.1f}/100。"},
            {"title": "收益表现", "content": f"近 1 月收益 {float(fund.get('return_1m') or 0):.2%}，近 3 月收益 {float(fund.get('return_3m') or 0):.2%}，近 6 月收益 {float(fund.get('return_6m') or 0):.2%}。"},
            {"title": "回撤与波动", "content": f"最大回撤 {float(fund.get('max_drawdown') or 0):.2%}，年化波动 {float(fund.get('volatility') or 0):.2%}。"},
            {"title": "评分来源", "content": f"趋势评分 {fund.get('trend_score')}，风险评分 {fund.get('risk_score')}，基金评分不使用股票基本面和估值模型。"},
            {"title": "风险点", "content": str(fund.get('risk_note') or "暂无风险说明。")},
            {"title": "操作边界", "content": "该结论用于基金观察和复盘，不构成自动申赎或交易指令。"},
        ]
        return self._record("fund", symbol, fund["nav_date"], sections)

    def _empty_result(self, analysis_type: str, target: str, message: str) -> dict:
        return {
            "analysis_type": analysis_type,
            "target": target,
            "data_version": None,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "sections": [{"title": "暂无数据", "content": message}],
        }

    def _record(self, analysis_type: str, target: str, data_version: str, sections: list[dict]) -> dict:
        generated_at = datetime.now().isoformat(timespec="seconds")
        result = {
            "analysis_type": analysis_type,
            "target": target,
            "data_version": data_version,
            "generated_at": generated_at,
            "sections": sections,
        }
        self.repo.execute(
            """
            INSERT INTO ai_analysis(analysis_type, target, data_version, prompt, result, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (analysis_type, target, data_version, "local-structured-explain", str(result), generated_at),
        )
        return result
