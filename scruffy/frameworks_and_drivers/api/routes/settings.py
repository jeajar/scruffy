"""Admin routes for application settings."""

import asyncio
import logging

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from scruffy.frameworks_and_drivers.api.auth import AdminUser
from scruffy.frameworks_and_drivers.database.settings_store import (
    get_extension_days,
    set_extension_days,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/settings", tags=["admin", "settings"])


class SettingsResponse(BaseModel):
    """Settings as returned by API."""

    extension_days: int


class SettingsUpdate(BaseModel):
    """Payload to update settings."""

    extension_days: int | None = Field(None, ge=1, le=365)


@router.get("", response_model=SettingsResponse)
async def get_settings(_user: AdminUser) -> SettingsResponse:
    """Get current admin settings. Admin only."""
    extension_days = await asyncio.to_thread(get_extension_days)
    return SettingsResponse(extension_days=extension_days)


@router.patch("", response_model=SettingsResponse)
async def update_settings(
    body: SettingsUpdate,
    _user: AdminUser,
) -> SettingsResponse:
    """Update admin settings. Admin only."""
    if body.extension_days is not None:
        await asyncio.to_thread(set_extension_days, body.extension_days)
        logger.info(
            "Settings updated",
            extra={"extension_days": body.extension_days},
        )
    extension_days = await asyncio.to_thread(get_extension_days)
    return SettingsResponse(extension_days=extension_days)
