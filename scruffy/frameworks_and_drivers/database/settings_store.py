"""Helpers for reading/writing admin settings from database."""

import logging
from typing import TYPE_CHECKING

from sqlmodel import Session, select

from scruffy.frameworks_and_drivers.config.settings import settings
from scruffy.interface_adapters.interfaces.settings_provider_interface import (
    EmailConfig,
)

if TYPE_CHECKING:
    from scruffy.domain.value_objects.retention_policy import RetentionPolicy
from scruffy.frameworks_and_drivers.database.database import get_engine
from scruffy.frameworks_and_drivers.database.settings_model import SettingsModel

logger = logging.getLogger(__name__)

EXTENSION_DAYS_KEY = "extension_days"
RETENTION_DAYS_KEY = "retention.retention_days"
REMINDER_DAYS_KEY = "retention.reminder_days"

# Services keys
SERVICES_OVERSEERR_URL = "services.overseerr_url"
SERVICES_OVERSEERR_API_KEY = "services.overseerr_api_key"
SERVICES_RADARR_URL = "services.radarr_url"
SERVICES_RADARR_API_KEY = "services.radarr_api_key"
SERVICES_SONARR_URL = "services.sonarr_url"
SERVICES_SONARR_API_KEY = "services.sonarr_api_key"

# Notifications keys
NOTIFICATIONS_EMAIL_ENABLED = "notifications.email.enabled"
NOTIFICATIONS_EMAIL_SMTP_HOST = "notifications.email.smtp_host"
NOTIFICATIONS_EMAIL_SMTP_PORT = "notifications.email.smtp_port"
NOTIFICATIONS_EMAIL_SMTP_USERNAME = "notifications.email.smtp_username"
NOTIFICATIONS_EMAIL_SMTP_PASSWORD = "notifications.email.smtp_password"
NOTIFICATIONS_EMAIL_SMTP_FROM_EMAIL = "notifications.email.smtp_from_email"
NOTIFICATIONS_EMAIL_SMTP_SSL_TLS = "notifications.email.smtp_ssl_tls"
NOTIFICATIONS_EMAIL_SMTP_STARTTLS = "notifications.email.smtp_starttls"


def _get(db_key: str) -> str | None:
    """Get raw value from DB. Returns None if not set."""
    engine = get_engine()
    with Session(engine) as session:
        model = session.get(SettingsModel, db_key)
        return model.value if model is not None else None


def _get_many(db_keys: list[str]) -> dict[str, str | None]:
    """Get multiple keys from DB in a single session. Returns dict of key -> value (None if not set)."""
    engine = get_engine()
    with Session(engine) as session:
        statement = select(SettingsModel).where(SettingsModel.key.in_(db_keys))
        rows = session.exec(statement).all()
        result = {k: None for k in db_keys}
        for row in rows:
            result[row.key] = row.value
        return result


def _set(key: str, value: str) -> None:
    """Set value in DB."""
    engine = get_engine()
    with Session(engine) as session:
        model = session.get(SettingsModel, key)
        if model is None:
            model = SettingsModel(key=key, value=value)
            session.add(model)
        else:
            model.value = value
        session.commit()


def get_extension_days() -> int:
    """
    Get extension_days setting.

    Resolution order: DB value if set, else env (settings.extension_days), else default 7.
    """
    val = _get(EXTENSION_DAYS_KEY)
    if val is not None:
        try:
            return int(val)
        except (ValueError, TypeError):
            logger.warning(
                "Invalid extension_days in DB, using env default",
                extra={"value": val},
            )
    return settings.extension_days


def set_extension_days(value: int) -> None:
    """Set extension_days in database."""
    _set(EXTENSION_DAYS_KEY, str(value))
    logger.info("Updated extension_days setting", extra={"value": value})


def get_retention_days() -> int:
    """
    Get retention_days setting.

    Resolution order: DB value if set, else env (settings.retention_days), else default 30.
    """
    val = _get(RETENTION_DAYS_KEY)
    if val is not None:
        try:
            return int(val)
        except (ValueError, TypeError):
            logger.warning(
                "Invalid retention_days in DB, using env default",
                extra={"value": val},
            )
    return settings.retention_days


def set_retention_days(value: int) -> None:
    """Set retention_days in database."""
    _set(RETENTION_DAYS_KEY, str(value))
    logger.info("Updated retention_days setting", extra={"value": value})


def get_reminder_days() -> int:
    """
    Get reminder_days setting.

    Resolution order: DB value if set, else env (settings.reminder_days), else default 7.
    """
    val = _get(REMINDER_DAYS_KEY)
    if val is not None:
        try:
            return int(val)
        except (ValueError, TypeError):
            logger.warning(
                "Invalid reminder_days in DB, using env default",
                extra={"value": val},
            )
    return settings.reminder_days


def set_reminder_days(value: int) -> None:
    """Set reminder_days in database."""
    _set(REMINDER_DAYS_KEY, str(value))
    logger.info("Updated reminder_days setting", extra={"value": value})


def get_retention_policy() -> "RetentionPolicy":
    """Get current retention policy from DB (with env fallback)."""
    from scruffy.domain.value_objects.retention_policy import RetentionPolicy

    return RetentionPolicy(
        retention_days=get_retention_days(),
        reminder_days=get_reminder_days(),
    )


# --- Services ---


def get_overseerr_url() -> str:
    """Get Overseerr URL. DB first, else env fallback."""
    val = _get(SERVICES_OVERSEERR_URL)
    return val if val else str(settings.overseerr_url)


def get_overseerr_api_key() -> str | None:
    """Get Overseerr API key. DB first, else env fallback."""
    val = _get(SERVICES_OVERSEERR_API_KEY)
    return val if val else settings.overseerr_api_key


def get_radarr_url() -> str:
    """Get Radarr URL. DB first, else env fallback."""
    val = _get(SERVICES_RADARR_URL)
    return val if val else str(settings.radarr_url)


def get_radarr_api_key() -> str | None:
    """Get Radarr API key. DB first, else env fallback."""
    val = _get(SERVICES_RADARR_API_KEY)
    return val if val else settings.radarr_api_key


def get_sonarr_url() -> str:
    """Get Sonarr URL. DB first, else env fallback."""
    val = _get(SERVICES_SONARR_URL)
    return val if val else str(settings.sonarr_url)


def get_sonarr_api_key() -> str | None:
    """Get Sonarr API key. DB first, else env fallback."""
    val = _get(SERVICES_SONARR_API_KEY)
    return val if val else settings.sonarr_api_key


_services_config_cache: "ServicesConfig | None" = None


def invalidate_services_config_cache() -> None:
    """Invalidate the services config cache. Call when services config is updated."""
    global _services_config_cache
    _services_config_cache = None


def set_services_config(
    *,
    overseerr_url: str | None = None,
    overseerr_api_key: str | None = None,
    radarr_url: str | None = None,
    radarr_api_key: str | None = None,
    sonarr_url: str | None = None,
    sonarr_api_key: str | None = None,
) -> None:
    """Set services config in database. Only provided keys are updated."""
    if overseerr_url is not None:
        _set(SERVICES_OVERSEERR_URL, overseerr_url)
    if overseerr_api_key is not None:
        _set(SERVICES_OVERSEERR_API_KEY, overseerr_api_key)
    if radarr_url is not None:
        _set(SERVICES_RADARR_URL, radarr_url)
    if radarr_api_key is not None:
        _set(SERVICES_RADARR_API_KEY, radarr_api_key)
    if sonarr_url is not None:
        _set(SERVICES_SONARR_URL, sonarr_url)
    if sonarr_api_key is not None:
        _set(SERVICES_SONARR_API_KEY, sonarr_api_key)
    invalidate_services_config_cache()
    logger.info("Updated services settings")


# --- Notifications (email) ---


def get_email_enabled() -> bool:
    """Get email enabled. DB first, else env fallback."""
    val = _get(NOTIFICATIONS_EMAIL_ENABLED)
    if val is not None:
        return val.lower() in ("true", "1", "yes")
    return settings.email_enabled


def get_smtp_host() -> str:
    val = _get(NOTIFICATIONS_EMAIL_SMTP_HOST)
    return val if val else settings.smtp_host


def get_smtp_port() -> int:
    val = _get(NOTIFICATIONS_EMAIL_SMTP_PORT)
    if val is not None:
        try:
            return int(val)
        except (ValueError, TypeError):
            pass
    return settings.smtp_port


def get_smtp_username() -> str | None:
    val = _get(NOTIFICATIONS_EMAIL_SMTP_USERNAME)
    return val if val else settings.smtp_username


def get_smtp_password() -> str | None:
    val = _get(NOTIFICATIONS_EMAIL_SMTP_PASSWORD)
    return val if val else settings.smtp_password


def get_smtp_from_email() -> str:
    val = _get(NOTIFICATIONS_EMAIL_SMTP_FROM_EMAIL)
    return val if val else str(settings.smtp_from_email)


def get_smtp_ssl_tls() -> bool:
    val = _get(NOTIFICATIONS_EMAIL_SMTP_SSL_TLS)
    if val is not None:
        return val.lower() in ("true", "1", "yes")
    return settings.smtp_ssl_tls


def get_smtp_starttls() -> bool:
    val = _get(NOTIFICATIONS_EMAIL_SMTP_STARTTLS)
    if val is not None:
        return val.lower() in ("true", "1", "yes")
    return settings.smtp_starttls


def get_email_config() -> EmailConfig:
    """Get full email config. DB first, else env fallback."""
    return EmailConfig(
        enabled=get_email_enabled(),
        smtp_host=get_smtp_host(),
        smtp_port=get_smtp_port(),
        smtp_username=get_smtp_username(),
        smtp_password=get_smtp_password(),
        smtp_from_email=get_smtp_from_email(),
        smtp_ssl_tls=get_smtp_ssl_tls(),
        smtp_starttls=get_smtp_starttls(),
    )


def set_email_config(
    *,
    enabled: bool | None = None,
    smtp_host: str | None = None,
    smtp_port: int | None = None,
    smtp_username: str | None = None,
    smtp_password: str | None = None,
    smtp_from_email: str | None = None,
    smtp_ssl_tls: bool | None = None,
    smtp_starttls: bool | None = None,
) -> None:
    """Set email config in database. Only provided keys are updated."""
    if enabled is not None:
        _set(NOTIFICATIONS_EMAIL_ENABLED, str(enabled).lower())
    if smtp_host is not None:
        _set(NOTIFICATIONS_EMAIL_SMTP_HOST, smtp_host)
    if smtp_port is not None:
        _set(NOTIFICATIONS_EMAIL_SMTP_PORT, str(smtp_port))
    if smtp_username is not None:
        _set(NOTIFICATIONS_EMAIL_SMTP_USERNAME, smtp_username)
    if smtp_password is not None:
        _set(NOTIFICATIONS_EMAIL_SMTP_PASSWORD, smtp_password)
    if smtp_from_email is not None:
        _set(NOTIFICATIONS_EMAIL_SMTP_FROM_EMAIL, smtp_from_email)
    if smtp_ssl_tls is not None:
        _set(NOTIFICATIONS_EMAIL_SMTP_SSL_TLS, str(smtp_ssl_tls).lower())
    if smtp_starttls is not None:
        _set(NOTIFICATIONS_EMAIL_SMTP_STARTTLS, str(smtp_starttls).lower())
    logger.info("Updated email notification settings")


# --- SettingsProvider (abstraction for gateways) ---

_SERVICES_KEYS = [
    SERVICES_OVERSEERR_URL,
    SERVICES_OVERSEERR_API_KEY,
    SERVICES_RADARR_URL,
    SERVICES_RADARR_API_KEY,
    SERVICES_SONARR_URL,
    SERVICES_SONARR_API_KEY,
]


def _build_services_config() -> "ServicesConfig":
    """Build ServicesConfig from DB using batched read. Used when cache is cold."""
    vals = _get_many(_SERVICES_KEYS)
    config = ServicesConfig()
    config.overseerr_url = vals.get(SERVICES_OVERSEERR_URL) or str(
        settings.overseerr_url
    )
    config.overseerr_api_key = (
        vals.get(SERVICES_OVERSEERR_API_KEY) or settings.overseerr_api_key
    )
    config.radarr_url = vals.get(SERVICES_RADARR_URL) or str(settings.radarr_url)
    config.radarr_api_key = vals.get(SERVICES_RADARR_API_KEY) or settings.radarr_api_key
    config.sonarr_url = vals.get(SERVICES_SONARR_URL) or str(settings.sonarr_url)
    config.sonarr_api_key = vals.get(SERVICES_SONARR_API_KEY) or settings.sonarr_api_key
    return config


class ServicesConfig:
    """Services configuration tuple: (overseerr_url, overseerr_api_key, radarr_url, radarr_api_key, sonarr_url, sonarr_api_key)."""

    def __init__(self) -> None:
        self.overseerr_url: str = ""
        self.overseerr_api_key: str | None = None
        self.radarr_url: str = ""
        self.radarr_api_key: str | None = None
        self.sonarr_url: str = ""
        self.sonarr_api_key: str | None = None


class SettingsProvider:
    """
    Provides runtime resolution of settings from DB (with env fallback).

    Gateways and EmailClient use this to get config at request time,
    supporting live config changes without restart.
    """

    def get_services_config(self) -> ServicesConfig:
        """Get current services config (Overseerr, Radarr, Sonarr). Cached until invalidated."""
        global _services_config_cache
        if _services_config_cache is None:
            _services_config_cache = _build_services_config()
        return _services_config_cache

    def get_email_config(self) -> EmailConfig:
        """Get current email config."""
        return get_email_config()
