from fastapi import APIRouter, Query

from app.services.fund_service import FundService

router = APIRouter(prefix="/funds", tags=["funds"])


@router.get("/analysis")
def get_fund_analysis(symbol: str | None = Query(default=None)) -> dict:
    return {"data": FundService().latest_analysis(symbol)}


@router.get("/{symbol}/nav")
def get_fund_nav(symbol: str, limit: int = Query(default=180, ge=1, le=1000)) -> dict:
    return {"data": FundService().latest_nav(symbol, limit)}
