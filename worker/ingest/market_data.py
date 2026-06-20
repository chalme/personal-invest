"""市场数据采集模块。

MVP 阶段保留接口边界；后续接入 AKShare / Tushare 后输出 raw 与 Parquet。
"""


def sync_market_data() -> dict:
    return {"status": "placeholder", "message": "market data ingestion boundary is ready"}

