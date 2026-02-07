"""Abstract settings provider interface for dependency inversion.

Implementations live in frameworks_and_drivers. Gateways and EmailClient depend on
this interface only, not on concrete database-backed implementations.
"""

from typing import Protocol, TypedDict


class IServicesConfig(Protocol):
    """Protocol for services configuration (Overseerr, Radarr, Sonarr)."""

    overseerr_url: str
    overseerr_api_key: str | None
    radarr_url: str
    radarr_api_key: str | None
    sonarr_url: str
    sonarr_api_key: str | None


class EmailConfig(TypedDict):
    """Email configuration dict."""

    enabled: bool
    smtp_host: str
    smtp_port: int
    smtp_username: str | None
    smtp_password: str | None
    smtp_from_email: str
    smtp_ssl_tls: bool
    smtp_starttls: bool


class ISettingsProvider(Protocol):
    """Abstract interface for runtime resolution of settings (DB + env fallback).

    Gateways and EmailClient use this to get config at request time,
    supporting live config changes without restart.
    """

    def get_services_config(self) -> IServicesConfig:
        """Get current services config (Overseerr, Radarr, Sonarr)."""
        ...

    def get_email_config(self) -> EmailConfig:
        """Get current email config."""
        ...

    def get_app_base_url(self) -> str:
        """Get app base URL for email links (instance address)."""
        ...
