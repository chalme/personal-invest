from fastapi import APIRouter, Query

from app.services.price_service import PriceService

router = APIRouter(prefix="/stocks", tags=["prices"])


@router.get("/{symbol}/prices")
def stock_prices(symbol: str, limit: int = Query(default=120, ge=1, le=500)) -> dict:
    return {"data": PriceService().latest_bars(symbol, limit)}
