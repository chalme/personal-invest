from fastapi import APIRouter

from app.services.review_service import ReviewService

router = APIRouter(prefix="/review", tags=["review"])


@router.get("/overview")
def get_review_overview() -> dict:
    return ReviewService().overview()
