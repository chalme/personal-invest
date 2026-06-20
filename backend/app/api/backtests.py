from fastapi import APIRouter, Query

from app.services.backtest_service import BacktestService

router = APIRouter(prefix="/backtests", tags=["backtests"])


@router.get("/watchlist")
def watchlist_backtest(
    initial_cash: float = Query(default=100000, ge=1000, le=100000000),
    limit: int = Query(default=500, ge=30, le=2000),
) -> dict:
    return {"data": BacktestService().watchlist_equal_weight(initial_cash=initial_cash, limit=limit)}
