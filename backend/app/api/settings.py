from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.services.settings_service import SettingsService

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("")
def get_settings() -> dict[str, Any]:
    return {"data": SettingsService().get_settings()}


@router.put("")
def update_settings(payload: dict[str, Any]) -> dict[str, Any]:
    return {"data": SettingsService().update_settings(payload)}


@router.post("/reset")
def reset_settings() -> dict[str, Any]:
    return {"data": SettingsService().reset_settings()}
