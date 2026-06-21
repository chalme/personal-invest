from __future__ import annotations

from typing import Any

from worker.storage import connect_db, now_iso, upsert_many


SAMPLE_PROFILES: dict[str, dict[str, float | str]] = {
    "600519.SH": {
        "source_mode": "SAMPLE",
        "revenue": 150_000_000_000,
        "net_profit": 74_000_000_000,
        "cash_flow": 84_000_000_000,
        "assets": 280_000_000_000,
        "liabilities": 62_000_000_000,
        "gross_margin": 0.91,
        "net_margin": 0.49,
        "pe": 28.0,
        "pb": 8.5,
        "ps": 13.6,
    },
    "000001.SZ": {
        "source_mode": "SAMPLE",
        "revenue": 165_000_000_000,
        "net_profit": 46_000_000_000,
        "cash_flow": 58_000_000_000,
        "assets": 5_700_000_000_000,
        "liabilities": 5_250_000_000_000,
        "gross_margin": 0.0,
        "net_margin": 0.28,
        "pe": 4.8,
        "pb": 0.55,
        "ps": 1.3,
    },
}


def _score(value: float, low: float, high: float) -> float:
    if high <= low:
        return 50.0
    return round(max(0.0, min(100.0, (value - low) / (high - low) * 100)), 2)


def _state(score: float) -> str:
    if score >= 80:
        return "高质量"
    if score >= 65:
        return "质量稳健"
    if score >= 50:
        return "中性观察"
    if score >= 35:
        return "质量承压"
    return "高风险"


def _stock_assets() -> list[dict[str, Any]]:
    with connect_db() as conn:
        rows = conn.execute(
            """
            SELECT symbol, name FROM instrument
            WHERE status = 'ACTIVE' AND UPPER(asset_type) = 'STOCK'
            UNION
            SELECT w.symbol, w.name
            FROM watchlist w
            LEFT JOIN instrument i ON i.symbol = w.symbol
            WHERE w.status = 'ACTIVE'
              AND UPPER(COALESCE(i.asset_type, w.asset_type)) = 'STOCK'
            ORDER BY symbol
            """
        ).fetchall()
    return [dict(row) for row in rows]


def _profile(symbol: str) -> dict[str, float | str]:
    if symbol in SAMPLE_PROFILES:
        return SAMPLE_PROFILES[symbol]
    seed = sum(ord(ch) for ch in symbol)
    scale = 1 + (seed % 7) / 10
    revenue = 18_000_000_000 * scale
    margin = 0.08 + (seed % 8) / 100
    assets = revenue * (2.3 + (seed % 4) / 5)
    liabilities = assets * (0.38 + (seed % 5) / 20)
    return {
        "source_mode": "ESTIMATED",
        "revenue": revenue,
        "net_profit": revenue * margin,
        "cash_flow": revenue * margin * (0.85 + (seed % 5) / 20),
        "assets": assets,
        "liabilities": liabilities,
        "gross_margin": 0.22 + (seed % 10) / 100,
        "net_margin": margin,
        "pe": 12 + (seed % 16),
        "pb": 1.0 + (seed % 18) / 10,
        "ps": 1.2 + (seed % 12) / 10,
    }


def calculate_stock_financials() -> dict[str, Any]:
    assets = _stock_assets()
    if not assets:
        return {"count": 0, "latest_data_date": None}

    now = now_iso()
    data_date = now[:10]
    statement_rows: list[tuple[Any, ...]] = []
    metric_rows: list[tuple[Any, ...]] = []
    valuation_rows: list[tuple[Any, ...]] = []
    quality_rows: list[tuple[Any, ...]] = []

    for asset in assets:
        symbol = str(asset["symbol"])
        name = str(asset.get("name") or symbol)
        p = _profile(symbol)
        revenue = float(p["revenue"])
        net_profit = float(p["net_profit"])
        cash_flow = float(p["cash_flow"])
        assets_total = float(p["assets"])
        liabilities = float(p["liabilities"])
        equity = max(1.0, assets_total - liabilities)
        gross_margin = float(p["gross_margin"])
        net_margin = float(p["net_margin"])
        debt_ratio = liabilities / assets_total if assets_total else 0.0
        roe = net_profit / equity if equity else 0.0
        roa = net_profit / assets_total if assets_total else 0.0
        cash_ratio = cash_flow / net_profit if net_profit else 0.0
        source_mode = str(p["source_mode"])
        source = "built_in_sample" if source_mode == "SAMPLE" else "deterministic_estimate"
        growth = 0.06 if source_mode == "SAMPLE" else 0.03
        profit_growth = 0.08 if source_mode == "SAMPLE" else 0.025
        quality_score = round(_score(roe, 0.03, 0.30) * 0.35 + _score(net_margin, 0.03, 0.35) * 0.25 + _score(cash_ratio, 0.5, 1.5) * 0.20 + (100 - _score(debt_ratio, 0.25, 0.85)) * 0.20, 2)
        growth_score = round((_score(growth, -0.05, 0.20) + _score(profit_growth, -0.08, 0.25)) / 2, 2)
        cash_score = _score(cash_ratio, 0.5, 1.5)
        balance_score = round(100 - _score(debt_ratio, 0.25, 0.85), 2)
        pe = float(p["pe"])
        pb = float(p["pb"])
        ps = float(p["ps"])
        pe_percentile = round(max(0, min(100, pe / 40 * 100)), 2)
        pb_percentile = round(max(0, min(100, pb / 10 * 100)), 2)
        valuation_score = round(100 - (pe_percentile * 0.6 + pb_percentile * 0.4), 2)
        total_score = round(quality_score * 0.35 + growth_score * 0.20 + cash_score * 0.15 + balance_score * 0.15 + valuation_score * 0.15, 2)
        version = f"stock_financial_{data_date}_{now}"
        statement_rows.append((data_date, "TTM", symbol, name, revenue, net_profit, cash_flow, assets_total, liabilities, equity, gross_margin, net_margin, debt_ratio, source, source_mode, data_date, version, now))
        metric_rows.append((data_date, symbol, name, growth, profit_growth, roe, roa, cash_ratio, gross_margin, net_margin, debt_ratio, quality_score, growth_score, cash_score, balance_score, source, source_mode, data_date, version, now))
        valuation_rows.append((data_date, symbol, name, pe, pb, ps, None, pe_percentile, pb_percentile, valuation_score, "估值偏低" if valuation_score >= 70 else "估值中性" if valuation_score >= 45 else "估值偏高", source, source_mode, data_date, version, now))
        quality_rows.append((data_date, symbol, name, total_score, _state(total_score), growth_score, quality_score, cash_score, balance_score, valuation_score, f"{name} 当前公司质量为{_state(total_score)}，数据来源为 {source_mode}。", "样本或估算财报仅用于展示和低置信度观察，不应单独触发高优先级建议。" if source_mode != "REAL" else "基于真实财报数据生成。", source, source_mode, data_date, version, now))

    with connect_db() as conn:
        statement_count = upsert_many(conn, """
            INSERT INTO financial_statement_snapshot(report_date, period_type, symbol, name, revenue, net_profit, operating_cash_flow, total_assets, total_liabilities, equity, gross_margin, net_margin, debt_ratio, source, source_mode, data_date, data_version, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(report_date, period_type, symbol) DO UPDATE SET name=excluded.name, revenue=excluded.revenue, net_profit=excluded.net_profit, operating_cash_flow=excluded.operating_cash_flow, total_assets=excluded.total_assets, total_liabilities=excluded.total_liabilities, equity=excluded.equity, gross_margin=excluded.gross_margin, net_margin=excluded.net_margin, debt_ratio=excluded.debt_ratio, source=excluded.source, source_mode=excluded.source_mode, data_date=excluded.data_date, data_version=excluded.data_version, created_at=excluded.created_at
        """, statement_rows)
        metric_count = upsert_many(conn, """
            INSERT INTO financial_metric_snapshot(metric_date, symbol, name, revenue_growth, net_profit_growth, roe, roa, operating_cash_flow_ratio, gross_margin, net_margin, debt_ratio, quality_score, growth_score, cashflow_score, balance_score, source, source_mode, data_date, data_version, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(metric_date, symbol) DO UPDATE SET name=excluded.name, revenue_growth=excluded.revenue_growth, net_profit_growth=excluded.net_profit_growth, roe=excluded.roe, roa=excluded.roa, operating_cash_flow_ratio=excluded.operating_cash_flow_ratio, gross_margin=excluded.gross_margin, net_margin=excluded.net_margin, debt_ratio=excluded.debt_ratio, quality_score=excluded.quality_score, growth_score=excluded.growth_score, cashflow_score=excluded.cashflow_score, balance_score=excluded.balance_score, source=excluded.source, source_mode=excluded.source_mode, data_date=excluded.data_date, data_version=excluded.data_version, created_at=excluded.created_at
        """, metric_rows)
        valuation_count = upsert_many(conn, """
            INSERT INTO valuation_snapshot(valuation_date, symbol, name, pe_ttm, pb, ps, dividend_yield, pe_percentile, pb_percentile, valuation_score, valuation_state, source, source_mode, data_date, data_version, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(valuation_date, symbol) DO UPDATE SET name=excluded.name, pe_ttm=excluded.pe_ttm, pb=excluded.pb, ps=excluded.ps, dividend_yield=excluded.dividend_yield, pe_percentile=excluded.pe_percentile, pb_percentile=excluded.pb_percentile, valuation_score=excluded.valuation_score, valuation_state=excluded.valuation_state, source=excluded.source, source_mode=excluded.source_mode, data_date=excluded.data_date, data_version=excluded.data_version, created_at=excluded.created_at
        """, valuation_rows)
        quality_count = upsert_many(conn, """
            INSERT INTO stock_quality_snapshot(quality_date, symbol, name, total_score, quality_state, growth_score, profitability_score, cashflow_score, balance_score, valuation_score, conclusion, risk_note, source, source_mode, data_date, data_version, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(quality_date, symbol) DO UPDATE SET name=excluded.name, total_score=excluded.total_score, quality_state=excluded.quality_state, growth_score=excluded.growth_score, profitability_score=excluded.profitability_score, cashflow_score=excluded.cashflow_score, balance_score=excluded.balance_score, valuation_score=excluded.valuation_score, conclusion=excluded.conclusion, risk_note=excluded.risk_note, source=excluded.source, source_mode=excluded.source_mode, data_date=excluded.data_date, data_version=excluded.data_version, created_at=excluded.created_at
        """, quality_rows)
    return {"count": quality_count, "statement_count": statement_count, "metric_count": metric_count, "valuation_count": valuation_count, "quality_count": quality_count, "latest_data_date": data_date}


if __name__ == "__main__":
    print(calculate_stock_financials())
