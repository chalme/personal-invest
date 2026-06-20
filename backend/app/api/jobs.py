from fastapi import APIRouter

from app.services.job_service import JobService
router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("")
def list_jobs() -> dict:
    return {"data": JobService().latest_jobs()}


@router.post("/daily")
def create_daily_job() -> dict:
    return JobService().create_daily_job()

