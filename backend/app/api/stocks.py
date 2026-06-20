from fastapi import APIRouter, Query

from app.services.stock_service import StockService
router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("/analysis")
def get_stock_analysis(symbol: str | None = Query(default=None)) -> dict:
    return {"data": StockService().latest_analysis(symbol)}

