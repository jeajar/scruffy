"""Admin routes for application settings."""

import asyncio
import logging

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from scruffy.frameworks_and_drivers.api.auth import AdminUser
from scruffy.frameworks_and_drivers.api.dependencies import ContainerDep
from scruffy.frameworks_and_drivers.database.settings_store import (
    get_email_config,
    get_extension_days,
    get_overseerr_api_key,
    get_overseerr_url,
    get_radarr_api_key,
    get_radarr_url,
    get_sonarr_api_key,
    get_sonarr_url,
    set_email_config,
    set_extension_days,
    set_services_config,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/settings", tags=["admin", "settings"])


# --- Response/Request models ---


class ServiceConfigResponse(BaseModel):
    """Service config as returned by API (api_key masked)."""

    url: str
    api_key_set: bool


class ServicesResponse(BaseModel):
    """Services section."""

    overseerr: ServiceConfigResponse
    radarr: ServiceConfigResponse
    sonarr: ServiceConfigResponse


class EmailConfigResponse(BaseModel):
    """Email config as returned by API (password masked)."""

    enabled: bool
    smtp_host: str
    smtp_port: int
    smtp_username: str | None
    smtp_password_set: bool
    smtp_from_email: str
    smtp_ssl_tls: bool
    smtp_starttls: bool


class NotificationsResponse(BaseModel):
    """Notifications section."""

    email: EmailConfigResponse


class SettingsResponse(BaseModel):
    """Settings as returned by API."""

    extension_days: int
    services: ServicesResponse
    notifications: NotificationsResponse


class ServiceConfigUpdate(BaseModel):
    """Partial service config update."""

    url: str | None = None
    api_key: str | None = None


class ServicesUpdate(BaseModel):
    """Partial services update."""

    overseerr: ServiceConfigUpdate | None = None
    radarr: ServiceConfigUpdate | None = None
    sonarr: ServiceConfigUpdate | None = None


class EmailConfigUpdate(BaseModel):
    """Partial email config update."""

    enabled: bool | None = None
    smtp_host: str | None = None
    smtp_port: int | None = Field(None, ge=1, le=65535)
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    smtp_ssl_tls: bool | None = None
    smtp_starttls: bool | None = None


class NotificationsUpdate(BaseModel):
    """Partial notifications update."""

    email: EmailConfigUpdate | None = None


class SettingsUpdate(BaseModel):
    """Payload to update settings."""

    extension_days: int | None = Field(None, ge=1, le=365)
    services: ServicesUpdate | None = None
    notifications: NotificationsUpdate | None = None


# --- Helpers ---


def _build_settings_response() -> SettingsResponse:
    """Build full settings response from store."""
    extension_days = get_extension_days()
    email_cfg = get_email_config()
    return SettingsResponse(
        extension_days=extension_days,
        services=ServicesResponse(
            overseerr=ServiceConfigResponse(
                url=get_overseerr_url(),
                api_key_set=bool(get_overseerr_api_key()),
            ),
            radarr=ServiceConfigResponse(
                url=get_radarr_url(),
                api_key_set=bool(get_radarr_api_key()),
            ),
            sonarr=ServiceConfigResponse(
                url=get_sonarr_url(),
                api_key_set=bool(get_sonarr_api_key()),
            ),
        ),
        notifications=NotificationsResponse(
            email=EmailConfigResponse(
                enabled=email_cfg["enabled"],
                smtp_host=email_cfg["smtp_host"],
                smtp_port=email_cfg["smtp_port"],
                smtp_username=email_cfg["smtp_username"],
                smtp_password_set=bool(email_cfg.get("smtp_password")),
                smtp_from_email=email_cfg["smtp_from_email"],
                smtp_ssl_tls=email_cfg["smtp_ssl_tls"],
                smtp_starttls=email_cfg["smtp_starttls"],
            ),
        ),
    )


# --- Routes ---


@router.get("", response_model=SettingsResponse)
async def get_settings(_user: AdminUser) -> SettingsResponse:
    """Get current admin settings. Admin only."""
    return await asyncio.to_thread(_build_settings_response)


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

    if body.services is not None:
        def _apply_services() -> None:
            if body.services.overseerr:
                set_services_config(
                    overseerr_url=body.services.overseerr.url,
                    overseerr_api_key=body.services.overseerr.api_key,
                )
            if body.services.radarr:
                set_services_config(
                    radarr_url=body.services.radarr.url,
                    radarr_api_key=body.services.radarr.api_key,
                )
            if body.services.sonarr:
                set_services_config(
                    sonarr_url=body.services.sonarr.url,
                    sonarr_api_key=body.services.sonarr.api_key,
                )

        await asyncio.to_thread(_apply_services)
        logger.info("Services settings updated")

    if body.notifications is not None and body.notifications.email is not None:
        e = body.notifications.email
        updates = e.model_dump(exclude_unset=True)
        if updates:
            await asyncio.to_thread(set_email_config, **updates)
            logger.info("Email notification settings updated")

    return await asyncio.to_thread(_build_settings_response)


@router.post("/services/test/{service}")
async def test_service_connection(
    service: str,
    _user: AdminUser,
    container: ContainerDep,
) -> dict:
    """
    Test connection to Overseerr, Radarr, or Sonarr.

    Service must be one of: overseerr, radarr, sonarr.
    """
    service = service.lower()
    if service == "overseerr":
        gateway = container.overseer_gateway
    elif service == "radarr":
        gateway = container.radarr_gateway
    elif service == "sonarr":
        gateway = container.sonarr_gateway
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown service: {service}. Use overseerr, radarr, or sonarr.",
        )

    ok = await gateway.status()
    return {
        "service": service,
        "status": "ok" if ok else "failed",
        "message": "Connection successful" if ok else "Connection failed",
    }
