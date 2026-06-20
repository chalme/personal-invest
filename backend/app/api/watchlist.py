from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.watchlist_service import WatchlistService
router = APIRouter(prefix="/watchlist", tags=["watchlist"])


class WatchlistCreate(BaseModel):
    symbol: str
    name: str | None = None
    asset_type: str | None = None
    market: str = "A_SHARE"
    group_name: str | None = None
    reason: str | None = None
    priority: int = Field(default=0, ge=0, le=10)


@router.get("")
def list_watchlist() -> dict:
    return {"data": WatchlistService().list_items()}


@router.post("")
def add_watchlist(payload: WatchlistCreate) -> dict:
    item_id = WatchlistService().add_item(payload.model_dump())
    return {"id": item_id, "status": "ok"}


@router.delete("/{symbol}")
def remove_watchlist(symbol: str) -> dict:
    WatchlistService().remove_item(symbol)
    return {"status": "ok"}

