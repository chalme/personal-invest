from fastapi import APIRouter, Query

from app.services.ai_service import AIService

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/market")
def explain_market() -> dict:
    return {"data": AIService().explain_market()}


@router.get("/portfolio")
def explain_portfolio() -> dict:
    return {"data": AIService().explain_portfolio()}


@router.get("/stock")
def explain_stock(symbol: str = Query(..., min_length=1)) -> dict:
    return {"data": AIService().explain_stock(symbol)}


@router.get("/fund")
def explain_fund(symbol: str = Query(..., min_length=1)) -> dict:
    return {"data": AIService().explain_fund(symbol)}


@router.get("/etf")
def explain_etf(symbol: str = Query(..., min_length=1)) -> dict:
    return {"data": AIService().explain_etf(symbol)}
