from fastapi import APIRouter, Query

from app.services.quote_service import QuoteService

router = APIRouter(prefix="/quotes", tags=["quotes"])


@router.get("/search")
def search_quotes(q: str = Query(..., min_length=1), limit: int = 20) -> dict:
    return {"data": QuoteService().search(q, limit=limit)}


@router.get("/{symbol}")
def get_quote(symbol: str) -> dict:
    return {"data": QuoteService().quote(symbol)}
