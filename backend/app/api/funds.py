from fastapi import APIRouter, Query

from app.services.fund_service import FundService
from app.services.fund_deep_service import FundDeepService
from app.services.etf_deep_service import EtfDeepService

router = APIRouter(prefix="/funds", tags=["funds"])


@router.get("/analysis")
def get_fund_analysis(symbol: str | None = Query(default=None)) -> dict:
    return {"data": FundService().latest_analysis(symbol)}


@router.get("/{symbol}/nav")
def get_fund_nav(symbol: str, limit: int = Query(default=180, ge=1, le=1000)) -> dict:
    return {"data": FundService().latest_nav(symbol, limit)}


@router.get("/{symbol}/deep")
def get_fund_deep(symbol: str) -> dict:
    return {"data": FundDeepService().latest(symbol)}


@router.get("/{symbol}/etf")
def get_etf_deep(symbol: str) -> dict:
    return {"data": EtfDeepService().latest(symbol)}
