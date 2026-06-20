from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.strategy_config_service import StrategyConfigService


router = APIRouter(tags=["strategies"])


class StrategyConfigPayload(BaseModel):
    strategy_code: str = Field(default="personal_watch_v1")
    strategy_name: str = Field(default="个人观察策略 V1")
    enabled: bool = True
    params: dict[str, float] = Field(default_factory=dict)


@router.get("/strategies")
def list_strategies() -> dict:
    return {"data": StrategyConfigService().list_configs()}


@router.get("/strategies/{strategy_code}")
def get_strategy(strategy_code: str) -> dict:
    try:
        return {"data": StrategyConfigService().get_config(strategy_code)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/strategies/{strategy_code}")
def update_strategy(strategy_code: str, payload: StrategyConfigPayload) -> dict:
    data = payload.model_dump()
    data["strategy_code"] = strategy_code
    return {"data": StrategyConfigService().upsert_config(data)}


@router.post("/strategies/{strategy_code}/reset")
def reset_strategy(strategy_code: str) -> dict:
    if strategy_code != "personal_watch_v1":
        raise HTTPException(status_code=404, detail="only personal_watch_v1 can be reset currently")
    return {"data": StrategyConfigService().reset_default_config()}
