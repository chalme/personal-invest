from fastapi import APIRouter, Query

from app.services.signal_service import SignalService

router = APIRouter(prefix="/signals", tags=["signals"])


@router.get("")
def latest_signals(limit: int = Query(default=100, ge=1, le=500)) -> dict:
    return {"data": SignalService().latest_signals(limit)}


@router.get("/{symbol}")
def signal_history(symbol: str, limit: int = Query(default=100, ge=1, le=500)) -> dict:
    return {"data": SignalService().signal_history(symbol, limit)}
