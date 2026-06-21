from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.review_service import ReviewService

router = APIRouter(prefix="/review", tags=["review"])


class ReviewTaskUpdate(BaseModel):
    status: str
    snoozed_until: str | None = None


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
