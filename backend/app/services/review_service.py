from __future__ import annotations

import json
from typing import Any

from app.repositories.sqlite_repo import SQLiteRepository
from app.services.data_source_service import DataSourceService


IMPORTANT_ADVICE_LEVELS = {"买入关注", "减仓关注", "卖出关注"}
IGNORED_RISK_TYPES = {"NO_MAJOR_RISK"}


class ReviewService:
    """Read-only review aggregation for the low-friction workbench."""

    def __init__(self, repo: SQLiteRepository | None = None) -> None:
        self.repo = repo or SQLiteRepository()

    def overview(self) -> dict[str, Any]:
        market = self._latest_market()
        data_status = self._data_status()
        latest_job = self._latest_job()
        risks = self._latest_actionable_risks()
        advice_changes = self._latest_advice_changes()
        latest_snapshot = self._latest_snapshot()
        previous_snapshot = self._previous_snapshot(latest_snapshot)
        portfolio_change = self._portfolio_change(latest_snapshot, previous_snapshot)
        important_items = self._important_items(
            market=market,
            data_status=data_status,
            latest_job=latest_job,
            risks=risks,
            advice_changes=advice_changes,
            portfolio_change=portfolio_change,
        )
        high_count = sum(1 for item in important_items if item.get("priority") == "HIGH")
        medium_count = sum(1 for item in important_items if item.get("priority") == "MEDIUM")
        intervention_required = high_count > 0 or medium_count > 0
        summary_message = (
            "今天有需要优先复核的重要事项。"
            if intervention_required
            else "暂无需要立即处理事项。"
        )
        return {
            "summary": {
                "intervention_required": intervention_required,
                "message": summary_message,
                "important_count": len(important_items),
                "high_count": high_count,
                "medium_count": medium_count,
                "market_state": market.get("trend_state") if market else None,
                "market_score": market.get("market_score") if market else None,
                "data_mode": data_status.get("mode"),
                "latest_data_date": data_status.get("latest_trade_date"),
                "latest_job_status": latest_job.get("status") if latest_job else None,
            },
            "important_items": important_items,
            "advice_changes": advice_changes,
            "portfolio_snapshot": {
                "latest": latest_snapshot,
                "previous": previous_snapshot,
                "change": portfolio_change,
            },
            "data_status": data_status,
            "market": market,
            "latest_job": latest_job,
            "review_windows": self._review_windows(),
        }

    def _latest_market(self) -> dict[str, Any] | None:
        return self.repo.fetch_one(
            "SELECT * FROM market_trend_snapshot ORDER BY trade_date DESC, id DESC LIMIT 1"
        )

    def _data_status(self) -> dict[str, Any]:
        return DataSourceService().market_source_summary()

    def _latest_job(self) -> dict[str, Any] | None:
        return self.repo.fetch_one("SELECT * FROM job_execution ORDER BY id DESC LIMIT 1")

    def _latest_actionable_risks(self) -> list[dict[str, Any]]:
        latest = self.repo.fetch_one("SELECT MAX(trade_date) AS trade_date FROM risk_event")
        trade_date = latest.get("trade_date") if latest else None
        if not trade_date:
            return []
        rows = self.repo.fetch_all(
            """
            SELECT * FROM risk_event
            WHERE trade_date = ?
              AND risk_type NOT IN ('NO_MAJOR_RISK')
              AND severity >= 2
            ORDER BY severity DESC, id DESC
            LIMIT 8
            """,
            (trade_date,),
        )
        return rows

    def _latest_advice_changes(self) -> list[dict[str, Any]]:
        latest = self.repo.fetch_one("SELECT MAX(advice_date) AS advice_date FROM investment_advice WHERE account_id = 1")
        advice_date = latest.get("advice_date") if latest else None
        if not advice_date:
            return []
        rows = self.repo.fetch_all(
            """
            SELECT * FROM investment_advice
            WHERE account_id = 1
              AND advice_date = ?
              AND (
                advice_level IN ('买入关注', '减仓关注', '卖出关注')
                OR (previous_advice_level IS NOT NULL AND previous_advice_level != advice_level)
              )
            ORDER BY confidence DESC, id DESC
            LIMIT 12
            """,
            (advice_date,),
        )
        return [self._decode_advice(row) for row in rows]

    def _decode_advice(self, row: dict[str, Any]) -> dict[str, Any]:
        item = dict(row)
        for field in ("key_metrics", "rule_result"):
            try:
                item[field] = json.loads(item.get(field) or "{}")
            except json.JSONDecodeError:
                item[field] = {}
        return item

    def _latest_snapshot(self) -> dict[str, Any] | None:
        return self.repo.fetch_one(
            """
            SELECT * FROM portfolio_snapshot
            WHERE account_id = 1
            ORDER BY snapshot_date DESC
            LIMIT 1
            """
        )

    def _previous_snapshot(self, latest_snapshot: dict[str, Any] | None) -> dict[str, Any] | None:
        if not latest_snapshot:
            return None
        return self.repo.fetch_one(
            """
            SELECT * FROM portfolio_snapshot
            WHERE account_id = 1 AND snapshot_date < ?
            ORDER BY snapshot_date DESC
            LIMIT 1
            """,
            (latest_snapshot.get("snapshot_date"),),
        )

    def _portfolio_change(
        self,
        latest: dict[str, Any] | None,
        previous: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if not latest:
            return None
        previous_value = float(previous.get("total_market_value") or 0) if previous else 0.0
        latest_value = float(latest.get("total_market_value") or 0)
        value_delta = latest_value - previous_value if previous else 0.0
        value_delta_ratio = (value_delta / previous_value) if previous_value > 0 else 0.0
        risk_delta = int(latest.get("risk_count") or 0) - int(previous.get("risk_count") or 0) if previous else 0
        return {
            "snapshot_date": latest.get("snapshot_date"),
            "previous_snapshot_date": previous.get("snapshot_date") if previous else None,
            "total_market_value": round(latest_value, 2),
            "value_delta": round(value_delta, 2),
            "value_delta_ratio": round(value_delta_ratio, 4),
            "total_pnl": round(float(latest.get("total_pnl") or 0), 2),
            "total_pnl_ratio": round(float(latest.get("total_pnl_ratio") or 0), 4),
            "risk_count": int(latest.get("risk_count") or 0),
            "risk_delta": risk_delta,
            "concentration_hhi": round(float(latest.get("concentration_hhi") or 0), 4),
        }

    def _important_items(
        self,
        *,
        market: dict[str, Any] | None,
        data_status: dict[str, Any],
        latest_job: dict[str, Any] | None,
        risks: list[dict[str, Any]],
        advice_changes: list[dict[str, Any]],
        portfolio_change: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        if latest_job and str(latest_job.get("status")) == "FAILED":
            items.append({
                "type": "JOB_FAILURE",
                "priority": "HIGH",
                "title": "最近一次每日更新失败",
                "message": latest_job.get("error") or latest_job.get("message") or "请重新执行今日更新。",
                "date": latest_job.get("finished_at") or latest_job.get("started_at"),
                "source": "job_execution",
            })
        if data_status.get("mode") in {"sample", "mixed", "unknown"}:
            priority = "MEDIUM" if data_status.get("mode") != "real" else "INFO"
            items.append({
                "type": "DATA_ISSUE",
                "priority": priority,
                "title": "数据可信度需要复核",
                "message": data_status.get("warning") or f"当前数据模式为 {data_status.get('mode') or 'unknown'}。",
                "date": data_status.get("latest_trade_date"),
                "source": "market_data_manifest",
            })
        if market and float(market.get("market_score") or 0) < 45:
            items.append({
                "type": "MARKET_CHANGE",
                "priority": "MEDIUM",
                "title": "市场环境偏弱",
                "message": market.get("summary") or "市场评分低于 45，新增风险暴露需要更谨慎。",
                "date": market.get("trade_date"),
                "source": "market_trend_snapshot",
            })
        for risk in risks:
            items.append({
                "type": "RISK",
                "priority": "HIGH" if int(risk.get("severity") or 0) >= 3 else "MEDIUM",
                "title": risk.get("risk_type") or "风险事件",
                "message": risk.get("message") or "存在需要复核的风险事件。",
                "date": risk.get("trade_date"),
                "symbol": risk.get("symbol"),
                "source": "risk_event",
            })
        for advice in advice_changes[:6]:
            level = str(advice.get("advice_level") or "")
            items.append({
                "type": "ADVICE_CHANGE",
                "priority": "HIGH" if level in {"减仓关注", "卖出关注"} else "MEDIUM",
                "title": f"{advice.get('name') or advice.get('symbol')}：{level}",
                "message": advice.get("one_liner") or advice.get("trigger_reason") or "建议发生变化，请复核。",
                "date": advice.get("advice_date"),
                "symbol": advice.get("symbol"),
                "source": "investment_advice",
            })
        if portfolio_change:
            if portfolio_change.get("risk_delta", 0) > 0:
                items.append({
                    "type": "PORTFOLIO_CHANGE",
                    "priority": "MEDIUM",
                    "title": "组合风险数量上升",
                    "message": f"风险数量较上一快照增加 {portfolio_change['risk_delta']} 条。",
                    "date": portfolio_change.get("snapshot_date"),
                    "source": "portfolio_snapshot",
                })
            if float(portfolio_change.get("concentration_hhi") or 0) >= 0.35:
                items.append({
                    "type": "PORTFOLIO_CHANGE",
                    "priority": "MEDIUM",
                    "title": "组合集中度偏高",
                    "message": f"当前集中度 HHI 为 {portfolio_change['concentration_hhi']:.2f}，需要检查单一资产暴露。",
                    "date": portfolio_change.get("snapshot_date"),
                    "source": "portfolio_snapshot",
                })
        priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "INFO": 3}
        return sorted(items, key=lambda item: (priority_order.get(str(item.get("priority")), 9), str(item.get("date") or "")), reverse=False)[:12]

    def _review_windows(self) -> dict[str, Any]:
        rows = self.repo.fetch_all(
            """
            SELECT snapshot_date, total_market_value, total_pnl, total_pnl_ratio, risk_count, advice_summary
            FROM portfolio_snapshot
            WHERE account_id = 1
            ORDER BY snapshot_date DESC
            LIMIT 30
            """
        )
        if not rows:
            return {"last_7_days": None, "last_30_days": None}
        ordered = list(reversed(rows))
        latest = ordered[-1]

        def window_summary(size: int) -> dict[str, Any] | None:
            window = ordered[-size:]
            if not window:
                return None
            first = window[0]
            value_delta = float(latest.get("total_market_value") or 0) - float(first.get("total_market_value") or 0)
            pnl_delta = float(latest.get("total_pnl") or 0) - float(first.get("total_pnl") or 0)
            return {
                "start_date": first.get("snapshot_date"),
                "end_date": latest.get("snapshot_date"),
                "days": len(window),
                "value_delta": round(value_delta, 2),
                "pnl_delta": round(pnl_delta, 2),
                "latest_risk_count": int(latest.get("risk_count") or 0),
            }

        return {"last_7_days": window_summary(7), "last_30_days": window_summary(30)}
