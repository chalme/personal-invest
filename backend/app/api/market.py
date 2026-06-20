from fastapi import APIRouter

from app.services.market_service import MarketService

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/data-source")
def get_market_data_source() -> dict:
    return {"data": MarketService().data_source_summary()}


@router.get("/trend")
def get_market_trend() -> dict:
    return {"data": MarketService().latest_market_trend()}


@router.get("/trend/history")
def get_market_trend_history(limit: int = 60) -> dict:
    return {"data": MarketService().market_history(limit)}


@router.get("/sectors")
def get_sector_trends() -> dict:
    return {"data": MarketService().latest_sectors()}


@router.get("/sectors/panorama")
def get_sector_panorama() -> dict:
    return {"data": MarketService().sector_panorama()}


@router.get("/sectors/history")
def get_sector_trend_history(limit: int = 20) -> dict:
    return {"data": MarketService().sector_history(limit)}
