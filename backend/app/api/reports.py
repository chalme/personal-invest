from fastapi import APIRouter, HTTPException, Query

from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/daily")
def daily_reports(limit: int = Query(default=30, ge=1, le=100)) -> dict:
    return {"data": ReportService().daily_reports(limit)}


@router.get("/daily/latest")
def latest_daily_report() -> dict:
    report = ReportService().latest_daily_report()
    if not report:
        raise HTTPException(status_code=404, detail="暂无日报")
    return {"data": report}


@router.get("/daily/{report_date}")
def daily_report(report_date: str) -> dict:
    report = ReportService().daily_report_by_date(report_date)
    if not report:
        raise HTTPException(status_code=404, detail="日报不存在")
    return {"data": report}
