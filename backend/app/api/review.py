from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.review_service import ReviewService

router = APIRouter(prefix="/review", tags=["review"])


class ReviewTaskUpdate(BaseModel):
    status: str
    snoozed_until: str | None = None


class DecisionCreate(BaseModel):
    symbol: str
    name: str | None = None
    asset_type: str | None = None
    decision_type: str
    decision_reason: str | None = None
    expected_outcome: str | None = None
    review_task_id: int | None = None
    advice_id: int | None = None
    advice_level: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    conviction: str | None = None
    data_date: str | None = None
    decision_date: str | None = None


@router.get("/overview")
def get_review_overview() -> dict:
    return ReviewService().overview()


@router.get("/tasks")
def list_review_tasks(
    status: str | None = Query(default="OPEN"),
    include_snoozed: bool = Query(default=False),
) -> dict:
    return {"data": ReviewService().list_tasks(status=status, include_snoozed=include_snoozed)}


@router.post("/tasks/generate")
def generate_review_tasks() -> dict:
    return ReviewService().sync_tasks_from_overview()


@router.patch("/tasks/{task_id}")
def update_review_task(task_id: int, payload: ReviewTaskUpdate) -> dict:
    try:
        task = ReviewService().update_task(task_id, payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"data": task}


@router.get("/decisions")
def list_decisions(symbol: str | None = Query(default=None)) -> dict:
    return {"data": ReviewService().list_decisions(symbol=symbol)}


@router.post("/decisions")
def create_decision(payload: DecisionCreate) -> dict:
    try:
        decision = ReviewService().create_decision(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"data": decision}
