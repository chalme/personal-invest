from fastapi import APIRouter

from app.services.market_service import MarketService
router = APIRouter(prefix="/market", tags=["market"])


@router.get("/trend")
def get_market_trend() -> dict:
    return {"data": MarketService().latest_market_trend()}


@router.get("/sectors")
def get_sector_trends() -> dict:
    return {"data": MarketService().latest_sectors()}

