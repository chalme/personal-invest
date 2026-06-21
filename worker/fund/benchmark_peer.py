from __future__ import annotations

from typing import Any

from worker.storage import connect_db


def _active_funds() -> int:
    with connect_db() as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM instrument
            WHERE status = 'ACTIVE' AND UPPER(asset_type) = 'FUND'
            """
        ).fetchone()
    return int(row["count"] or 0) if row else 0


def build_fund_benchmark_peer_exposure() -> dict[str, Any]:
    """Fund benchmark / peer / exposure real-only pipeline.

    No real benchmark, peer ranking, or holding exposure provider is connected yet.
    Runtime must not synthesize benchmark returns, percentile ranks, or exposure rows.
    """
    active_count = _active_funds()
    if active_count <= 0:
        return {"status": "skipped", "count": 0, "reason": "no active FUND assets"}
    return {
        "status": "missing",
        "count": 0,
        "benchmark_count": 0,
        "peer_count": 0,
        "exposure_count": 0,
        "asset_count": active_count,
        "reason": "real fund benchmark/peer/exposure source is not connected",
    }


if __name__ == "__main__":
    print(build_fund_benchmark_peer_exposure())
