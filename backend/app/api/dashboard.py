from fastapi import APIRouter

from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("")
def get_dashboard() -> dict:
    return DashboardService().get_dashboard()

