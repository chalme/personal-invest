from __future__ import annotations

from typing import Any

from worker.storage import connect_db, now_iso, upsert_many


def build_fund_benchmark_peer_exposure() -> dict[str, Any]:
    now = now_iso()
    today = now[:10]
    with connect_db() as conn:
        profiles = conn.execute(
            """
            SELECT p.symbol, p.name, p.fund_type, p.benchmark,
                   r.return_3m, r.return_6m, r.risk_return_score, r.source_mode, r.data_date
            FROM fund_profile p
            LEFT JOIN fund_risk_return_snapshot r
              ON r.symbol = p.symbol
             AND r.snapshot_date = (
                SELECT MAX(snapshot_date) FROM fund_risk_return_snapshot WHERE symbol = p.symbol
             )
            ORDER BY p.symbol
            """
        ).fetchall()
    if not profiles:
        return {"status": "skipped", "count": 0, "reason": "no fund_profile rows"}

    benchmark_rows: list[tuple[Any, ...]] = []
    peer_rows: list[tuple[Any, ...]] = []
    exposure_rows: list[tuple[Any, ...]] = []
    for row in profiles:
        symbol = str(row["symbol"])
        name = str(row["name"] or symbol)
        source_mode = str(row["source_mode"] or "SAMPLE")
        data_date = str(row["data_date"] or today)
        ret_3m = row["return_3m"]
        ret_6m = row["return_6m"]
        benchmark_return = 0.03 if ret_3m is not None else None
        excess = round(float(ret_3m) - benchmark_return, 4) if ret_3m is not None else None
        benchmark_score = round(max(0, min(100, 50 + (excess or 0) * 350)), 2) if excess is not None else 45.0
        percentile_3m = round(max(0, min(100, 55 + float(ret_3m or 0) * 260)), 2)
        percentile_6m = round(max(0, min(100, 55 + float(ret_6m or 0) * 180)), 2)
        peer_score = round((percentile_3m + percentile_6m) / 2, 2)
        version = f"fund_benchmark_peer_{data_date}_{now}"
        benchmark_rows.append((data_date, symbol, name, row["benchmark"] or "待补充基准", ret_3m, benchmark_return, excess, benchmark_score, "built_in_sample", source_mode, data_date, version, now))
        peer_rows.append((data_date, symbol, name, row["fund_type"] or "ACTIVE_EQUITY", percentile_3m, percentile_6m, peer_score, "同类分位为样本/估算口径，待接入真实同类数据源。", "built_in_sample", source_mode, data_date, version, now))
        exposure_rows.extend([
            (data_date, symbol, name, "STYLE", "主动权益", 0.55, "样本暴露，仅用于识别组合重复暴露的字段占位。", "built_in_sample", source_mode, data_date, version, now),
            (data_date, symbol, name, "SECTOR", "消费", 0.25, "样本行业暴露，待接入真实持仓。", "built_in_sample", source_mode, data_date, version, now),
            (data_date, symbol, name, "SECTOR", "科技", 0.20, "样本行业暴露，待接入真实持仓。", "built_in_sample", source_mode, data_date, version, now),
        ])

    with connect_db() as conn:
        benchmark_count = upsert_many(conn, """
            INSERT INTO fund_benchmark_snapshot(snapshot_date, symbol, name, benchmark_name, fund_return_3m, benchmark_return_3m, excess_return_3m, benchmark_score, source, source_mode, data_date, data_version, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(snapshot_date, symbol) DO UPDATE SET
                name=excluded.name, benchmark_name=excluded.benchmark_name,
                fund_return_3m=excluded.fund_return_3m, benchmark_return_3m=excluded.benchmark_return_3m,
                excess_return_3m=excluded.excess_return_3m, benchmark_score=excluded.benchmark_score,
                source=excluded.source, source_mode=excluded.source_mode,
                data_date=excluded.data_date, data_version=excluded.data_version, created_at=excluded.created_at
        """, benchmark_rows)
        peer_count = upsert_many(conn, """
            INSERT INTO fund_peer_rank_snapshot(snapshot_date, symbol, name, peer_group, percentile_3m, percentile_6m, peer_score, peer_note, source, source_mode, data_date, data_version, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(snapshot_date, symbol) DO UPDATE SET
                name=excluded.name, peer_group=excluded.peer_group,
                percentile_3m=excluded.percentile_3m, percentile_6m=excluded.percentile_6m,
                peer_score=excluded.peer_score, peer_note=excluded.peer_note,
                source=excluded.source, source_mode=excluded.source_mode,
                data_date=excluded.data_date, data_version=excluded.data_version, created_at=excluded.created_at
        """, peer_rows)
        exposure_count = upsert_many(conn, """
            INSERT INTO fund_holding_exposure_snapshot(snapshot_date, symbol, name, exposure_type, exposure_name, weight, overlap_note, source, source_mode, data_date, data_version, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(snapshot_date, symbol, exposure_type, exposure_name) DO UPDATE SET
                name=excluded.name, weight=excluded.weight, overlap_note=excluded.overlap_note,
                source=excluded.source, source_mode=excluded.source_mode,
                data_date=excluded.data_date, data_version=excluded.data_version, created_at=excluded.created_at
        """, exposure_rows)
    return {"status": "ok", "count": benchmark_count, "benchmark_count": benchmark_count, "peer_count": peer_count, "exposure_count": exposure_count}


if __name__ == "__main__":
    print(build_fund_benchmark_peer_exposure())
