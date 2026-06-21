from __future__ import annotations

from typing import Any

from worker.storage import connect_db, now_iso, upsert_many


def _etf_assets() -> list[dict[str, Any]]:
    with connect_db() as conn:
        rows = conn.execute(
            """
            SELECT symbol, name, asset_type, market, exchange, sector_code, sector_name, fund_type, risk_level
            FROM instrument
            WHERE status = 'ACTIVE'
              AND UPPER(asset_type) IN ('ETF', 'LOF')
            ORDER BY symbol
            """
        ).fetchall()
    return [dict(row) for row in rows]


def _guess_index(symbol: str, name: str, sector_name: str | None) -> tuple[str, str, str]:
    text = f"{symbol} {name} {sector_name or ''}".lower()
    if "300" in text or "沪深300" in name:
        return "BROAD_INDEX", "沪深300", "宽基"
    if "500" in text or "中证500" in name:
        return "BROAD_INDEX", "中证500", "宽基"
    if "创业" in name or "科创" in name:
        return "GROWTH_INDEX", "成长指数", "成长"
    if sector_name:
        return "SECTOR_THEME", f"{sector_name}指数", sector_name
    return "UNKNOWN", "待补充跟踪指数", "待补充主题"


def _exposures(symbol: str, name: str, market: str | None, sector_name: str | None, theme: str) -> list[tuple[str, str, float | None, str]]:
    rows: list[tuple[str, str, float | None, str]] = []
    rows.append(("ASSET_CLASS", "权益", 1.0, "基于 ETF 类型的估算资产类别暴露。"))
    if market:
        rows.append(("REGION", str(market), 1.0, "基于市场代码的估算地区暴露。"))
    if sector_name:
        rows.append(("SECTOR", sector_name, 1.0, "基于 instrument 行业字段的估算行业暴露。"))
    if theme and theme != "待补充主题":
        rows.append(("THEME", theme, 1.0, "基于 ETF 名称和行业字段的估算主题暴露。"))
    if not rows:
        rows.append(("UNKNOWN", "待补充暴露", None, "缺少 ETF 暴露数据，等待真实数据源补齐。"))
    return rows


def build_etf_profile_exposure() -> dict[str, Any]:
    assets = _etf_assets()
    if not assets:
        return {"status": "skipped", "count": 0, "reason": "no active ETF or LOF assets"}

    now = now_iso()
    today = now[:10]
    profile_rows: list[tuple[Any, ...]] = []
    exposure_rows: list[tuple[Any, ...]] = []

    for asset in assets:
        symbol = str(asset["symbol"])
        name = str(asset.get("name") or symbol)
        market = asset.get("market")
        exchange = asset.get("exchange") or market
        sector_name = asset.get("sector_name")
        etf_type, tracking_index, theme = _guess_index(symbol, name, sector_name)
        source_mode = "ESTIMATED"
        data_version = f"etf_profile_exposure_{today}_{now}"
        profile_rows.append(
            (
                symbol,
                name,
                etf_type,
                tracking_index,
                theme,
                "待补充基金公司",
                exchange,
                "instrument_estimate",
                source_mode,
                today,
                data_version,
                now,
            )
        )
        for exposure_type, exposure_name, weight, note in _exposures(symbol, name, market, sector_name, theme):
            exposure_rows.append(
                (
                    today,
                    symbol,
                    name,
                    exposure_type,
                    exposure_name,
                    weight,
                    note,
                    "instrument_estimate",
                    source_mode,
                    today,
                    data_version,
                    now,
                )
            )

    with connect_db() as conn:
        profile_count = upsert_many(
            conn,
            """
            INSERT INTO etf_profile(symbol, name, etf_type, tracking_index, theme, fund_company, listing_exchange, source, source_mode, data_date, data_version, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(symbol) DO UPDATE SET
                name=excluded.name,
                etf_type=excluded.etf_type,
                tracking_index=excluded.tracking_index,
                theme=excluded.theme,
                fund_company=excluded.fund_company,
                listing_exchange=excluded.listing_exchange,
                source=excluded.source,
                source_mode=excluded.source_mode,
                data_date=excluded.data_date,
                data_version=excluded.data_version,
                updated_at=excluded.updated_at
            """,
            profile_rows,
        )
        exposure_count = upsert_many(
            conn,
            """
            INSERT INTO etf_exposure_snapshot(snapshot_date, symbol, name, exposure_type, exposure_name, weight, exposure_note, source, source_mode, data_date, data_version, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(snapshot_date, symbol, exposure_type, exposure_name) DO UPDATE SET
                name=excluded.name,
                weight=excluded.weight,
                exposure_note=excluded.exposure_note,
                source=excluded.source,
                source_mode=excluded.source_mode,
                data_date=excluded.data_date,
                data_version=excluded.data_version,
                created_at=excluded.created_at
            """,
            exposure_rows,
        )
    return {"status": "ok", "count": profile_count, "profile_count": profile_count, "exposure_count": exposure_count}


if __name__ == "__main__":
    print(build_etf_profile_exposure())
