from fastapi import APIRouter
from pydantic import BaseModel

from app.services.portfolio_service import PortfolioService
router = APIRouter(prefix="/portfolio", tags=["portfolio"])


class PositionUpsert(BaseModel):
    account_id: int = 1
    symbol: str
    name: str | None = None
    quantity: float
    avg_cost: float
    current_price: float | None = None
    position_ratio: float = 0
    buy_reason: str | None = None
    stop_loss_price: float | None = None
    take_profit_price: float | None = None


@router.get("/positions")
def list_positions() -> dict:
    return {"data": PortfolioService().list_positions()}


@router.get("/overview")
def get_portfolio_overview() -> dict:
    return {"data": PortfolioService().portfolio_overview()}


@router.post("/positions")
def upsert_position(payload: PositionUpsert) -> dict:
    item_id = PortfolioService().upsert_position(payload.model_dump())
    return {"id": item_id, "status": "ok"}


@router.delete("/positions/{symbol}")
def remove_position(symbol: str, account_id: int = 1) -> dict:
    PortfolioService().remove_position(symbol=symbol, account_id=account_id)
    return {"status": "ok"}

