from fastapi import APIRouter, Query

from app.services.stock_service import StockService
from app.services.stock_financial_service import StockFinancialService
router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("/analysis")
def get_stock_analysis(symbol: str | None = Query(default=None)) -> dict:
    return {"data": StockService().latest_analysis(symbol)}



@router.get("/{symbol}/financial")
def get_stock_financial(symbol: str) -> dict:
    return {"data": StockFinancialService().latest(symbol)}


@router.get("/financial/summary")
def get_stock_financial_summary() -> dict:
    return {"data": StockFinancialService().latest_all()}
