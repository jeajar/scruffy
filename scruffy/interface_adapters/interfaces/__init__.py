"""Abstract interfaces for external dependencies (e.g. HTTP, settings)."""

from scruffy.interface_adapters.interfaces.http_client_interface import (
    HttpRequestError,
    IHttpClient,
)
from scruffy.interface_adapters.interfaces.settings_provider_interface import (
    EmailConfig,
    ISettingsProvider,
)

__all__ = [
    "EmailConfig",
    "HttpClientInterface",
    "HttpRequestError",
    "SettingsProviderInterface",
]
