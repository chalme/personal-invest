from __future__ import annotations

from typing import Any

from worker.storage import connect_db


def _active_etfs() -> int:
    with connect_db() as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM instrument
            WHERE status = 'ACTIVE'
              AND UPPER(asset_type) IN ('ETF', 'LOF')
            """
        ).fetchone()
    return int(row["count"] or 0) if row else 0


def build_etf_profile_exposure() -> dict[str, Any]:
    """ETF profile / exposure real-only pipeline.

    No real ETF profile, constituent, or exposure provider is connected yet.
    Runtime must not infer tracking indexes, themes, companies, or exposure weights.
    """
    active_count = _active_etfs()
    if active_count <= 0:
        return {"status": "skipped", "count": 0, "reason": "no active ETF or LOF assets"}
    return {
        "status": "missing",
        "count": 0,
        "profile_count": 0,
        "exposure_count": 0,
        "asset_count": active_count,
        "reason": "real ETF profile/exposure source is not connected",
    }


if __name__ == "__main__":
    print(build_etf_profile_exposure())
