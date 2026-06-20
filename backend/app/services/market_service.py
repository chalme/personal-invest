from app.repositories.sqlite_repo import SQLiteRepository
from app.services.data_source_service import DataSourceService


DEFENSIVE_KEYWORDS = ("银行", "红利", "债", "现金", "货币", "公用", "电力", "高股息", "防守")


def _sector_category(row: dict) -> tuple[str, str]:
    score = float(row.get("trend_score") or 0)
    momentum_20 = float(row.get("momentum_20") or 0)
    momentum_60 = float(row.get("momentum_60") or 0)
    volume_change = float(row.get("volume_change") or 0)
    name = str(row.get("sector_name") or "")
    if score >= 80 or (momentum_20 >= 0.08 and volume_change >= 0.5):
        return "overheat", "过热方向"
    if score >= 65:
        return "hot", "热门方向"
    if any(keyword in name for keyword in DEFENSIVE_KEYWORDS) and score >= 45:
        return "defensive", "防守方向"
    if momentum_20 > 0 and momentum_60 <= 0.02 and volume_change > 0:
        return "rotation", "轮动方向"
    if score < 45:
        return "cold", "冷门方向"
    return "neutral", "中性观察"


def _sector_explanation(row: dict, label: str) -> str:
    score = float(row.get("trend_score") or 0)
    momentum_20 = float(row.get("momentum_20") or 0)
    momentum_60 = float(row.get("momentum_60") or 0)
    volume_change = float(row.get("volume_change") or 0)
    return f"{label}：评分 {score:.1f}，20日动量 {momentum_20:.2%}，60日动量 {momentum_60:.2%}，量能变化 {volume_change:.2%}。"


class MarketService:
    def __init__(self, repo: SQLiteRepository | None = None) -> None:
        self.repo = repo or SQLiteRepository()

    def _sector_mapped_assets(self) -> dict[str, list[dict]]:
        mapped_rows = self.repo.fetch_all(
            """
            SELECT
                m.sector_code,
                m.sector_name,
                m.map_type,
                m.weight,
                m.source,
                i.symbol,
                COALESCE(i.name, w.name, m.symbol) AS name,
                COALESCE(i.asset_type, w.asset_type) AS asset_type,
                w.group_name,
                w.reason,
                w.priority,
                COALESCE(w.status, i.status) AS status
            FROM instrument_sector_map m
            LEFT JOIN instrument i ON i.symbol = m.symbol
            LEFT JOIN watchlist w ON w.symbol = m.symbol AND w.status = 'ACTIVE'
            WHERE COALESCE(w.status, i.status) = 'ACTIVE'
            ORDER BY COALESCE(w.priority, 0) DESC, m.weight DESC
            """
        )
        assets_by_group: dict[str, list[dict]] = {}
        for item in mapped_rows:
            key = str(item.get("sector_code") or item.get("sector_name") or "未分组").upper().replace(" ", "_")
            assets_by_group.setdefault(key, []).append(item)
        return assets_by_group

    def latest_market_trend(self) -> dict | None:
        return self.repo.fetch_one(
            "SELECT * FROM market_trend_snapshot ORDER BY trade_date DESC, id DESC LIMIT 1"
        )

    def market_history(self, limit: int = 60) -> list[dict]:
        safe_limit = max(1, min(int(limit or 60), 240))
        rows = self.repo.fetch_all(
            """
            SELECT
                trade_date,
                market_score,
                trend_state,
                index_trend_score,
                breadth_score,
                volume_score,
                sector_score,
                sentiment_score,
                fund_flow_score,
                summary
            FROM market_trend_snapshot
            ORDER BY trade_date DESC, id DESC
            LIMIT ?
            """,
            (safe_limit,),
        )
        return list(reversed(rows))

    def latest_sectors(self) -> list[dict]:
        return self.repo.fetch_all(
            """
            SELECT * FROM sector_trend_snapshot
            WHERE trade_date = (SELECT MAX(trade_date) FROM sector_trend_snapshot)
            ORDER BY rank ASC, trend_score DESC
            """
        )

    def sector_panorama(self) -> dict:
        sectors = self.latest_sectors()
        watchlist = self.repo.fetch_all(
            """
            SELECT symbol, name, asset_type, group_name, reason, priority, status
            FROM watchlist
            WHERE status = 'ACTIVE'
            ORDER BY priority DESC, updated_at DESC
            """
        )
        assets_by_group = self._sector_mapped_assets()
        mapped_symbols = {
            (key, str(item.get("symbol")))
            for key, items in assets_by_group.items()
            for item in items
        }
        for item in watchlist:
            key = str(item.get("group_name") or "未分组").upper().replace(" ", "_")
            if (key, str(item.get("symbol"))) in mapped_symbols:
                continue
            item = {**item, "map_type": "FALLBACK", "weight": 1.0, "source": "WATCHLIST_GROUP"}
            assets_by_group.setdefault(key, []).append(item)

        groups: dict[str, list[dict]] = {key: [] for key in ["overheat", "hot", "rotation", "defensive", "cold", "neutral"]}
        labels = {
            "overheat": "过热方向",
            "hot": "热门方向",
            "rotation": "轮动方向",
            "defensive": "防守方向",
            "cold": "冷门方向",
            "neutral": "中性观察",
        }
        enriched: list[dict] = []
        for row in sectors:
            category, label = _sector_category(row)
            sector_code = str(row.get("sector_code") or "")
            item = {
                **row,
                "category": category,
                "category_label": label,
                "explanation": _sector_explanation(row, label),
                "mapped_assets": assets_by_group.get(sector_code, []),
            }
            groups.setdefault(category, []).append(item)
            enriched.append(item)

        summary = {
            "trade_date": enriched[0].get("trade_date") if enriched else None,
            "total_sector_count": len(enriched),
            "overheat_count": len(groups.get("overheat", [])),
            "hot_count": len(groups.get("hot", [])),
            "rotation_count": len(groups.get("rotation", [])),
            "defensive_count": len(groups.get("defensive", [])),
            "cold_count": len(groups.get("cold", [])),
            "top_sector": enriched[0] if enriched else None,
            "bottom_sector": enriched[-1] if enriched else None,
            "main_message": self._sector_main_message(groups, enriched),
        }
        return {"summary": summary, "groups": groups, "labels": labels, "sectors": enriched}

    def _sector_main_message(self, groups: dict[str, list[dict]], sectors: list[dict]) -> str:
        if not sectors:
            return "暂无行业全景数据，请先执行每日更新。"
        hot_names = "、".join(item["sector_name"] for item in (groups.get("hot", []) + groups.get("overheat", []))[:3])
        cold_names = "、".join(item["sector_name"] for item in groups.get("cold", [])[:3])
        rotation_names = "、".join(item["sector_name"] for item in groups.get("rotation", [])[:3])
        parts = []
        if hot_names:
            parts.append(f"强势集中在 {hot_names}")
        if rotation_names:
            parts.append(f"轮动线索包括 {rotation_names}")
        if cold_names:
            parts.append(f"弱势方向主要是 {cold_names}")
        return "；".join(parts) + "。" if parts else "行业整体偏中性，等待更明确的轮动方向。"

    def sector_history(self, limit: int = 20) -> list[dict]:
        safe_limit = max(1, min(int(limit or 20), 120))
        dates = self.repo.fetch_all(
            """
            SELECT DISTINCT trade_date
            FROM sector_trend_snapshot
            ORDER BY trade_date DESC
            LIMIT ?
            """,
            (safe_limit,),
        )
        if not dates:
            return []

        min_date = min(item["trade_date"] for item in dates)
        return self.repo.fetch_all(
            """
            SELECT
                trade_date,
                sector_code,
                sector_name,
                trend_score,
                rank,
                state,
                momentum_20,
                momentum_60,
                volume_change
            FROM sector_trend_snapshot
            WHERE trade_date >= ?
            ORDER BY trade_date ASC, rank ASC
            """,
            (min_date,),
        )

    def data_source_summary(self) -> dict:
        return DataSourceService().market_source_summary()

