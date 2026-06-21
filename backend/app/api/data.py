from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.services.data_credibility_service import DataCredibilityService

router = APIRouter(prefix="/data", tags=["data"])


@router.get("/credibility")
def get_data_credibility() -> dict[str, Any]:
    return {"data": DataCredibilityService().overview()}
