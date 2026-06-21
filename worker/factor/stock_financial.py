from __future__ import annotations

from typing import Any

from worker.storage import connect_db


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


def calculate_stock_financials() -> dict[str, Any]:
    """Stock financial real-only pipeline.

    The project has not connected a real financial statement / valuation source yet.
    Runtime must not synthesize built-in samples or deterministic estimates; historical
    non-real records are handled by the real-only purge script.
    """
    assets = _stock_assets()
    if not assets:
        return {"status": "skipped", "count": 0, "latest_data_date": None}
    return {
        "status": "missing",
        "count": 0,
        "latest_data_date": None,
        "asset_count": len(assets),
        "reason": "real stock financial source is not connected",
    }


if __name__ == "__main__":
    print(calculate_stock_financials())
