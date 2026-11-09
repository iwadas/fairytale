from typing import Optional

from fastapi import APIRouter

from app.api.deps import SessionDep
from app.schemas.settings import SettingsOut, UpdateSettingsIn
from app.services import settings_service

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=Optional[SettingsOut])
async def get_settings(session: SessionDep):
    settings = await settings_service.get_settings(session)
    return SettingsOut.from_model(settings) if settings else None


@router.put("")
async def update_settings(session: SessionDep, body: Optional[UpdateSettingsIn] = None):
    updated = await settings_service.update_settings(session, body or UpdateSettingsIn())
    return {"message": "Settings updated successfully", "settings": updated}
