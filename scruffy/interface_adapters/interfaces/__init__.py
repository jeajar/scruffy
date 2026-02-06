"""Abstract interfaces for external dependencies (e.g. HTTP)."""

from scruffy.interface_adapters.interfaces.http_client_interface import (
    HttpRequestError,
    HttpClientInterface,
)

__all__ = ["HttpClientInterface", "HttpRequestError"]
