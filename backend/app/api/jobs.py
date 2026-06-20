from fastapi import APIRouter
from fastapi import HTTPException

from app.services.job_service import JobService
router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("")
def list_jobs() -> dict:
    return {"data": JobService().latest_jobs()}


@router.post("/daily")
def create_daily_job() -> dict:
    return JobService().create_daily_job()


@router.get("/{job_id}")
def get_job(job_id: int) -> dict:
    job = JobService().get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {"data": job}

