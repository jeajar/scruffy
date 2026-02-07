"""Abstract HTTP client interface for dependency inversion.

Implementations live in frameworks_and_drivers. Gateways depend on this
interface only, not on concrete HTTP libraries.
"""

from abc import ABC, abstractmethod
from typing import Any


class HttpRequestError(Exception):
    """Raised by HttpClient implementations when a request fails.

    Covers connection failures, timeouts, and HTTP errors. Callers in
    interface_adapters can catch this without depending on the underlying
    transport (e.g. httpx).
    """


class IHttpClient(ABC):
    """Abstract interface for making HTTP requests."""

    @abstractmethod
    async def get(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make GET request and return JSON response.

        Raises HttpRequestError on connection failure, timeout, or HTTP error.
        """
        ...

    @abstractmethod
    async def delete(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
    ) -> None:
        """Make DELETE request.

        Raises HttpRequestError on connection failure, timeout, or HTTP error.
        """
        ...

    @abstractmethod
    async def put(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make PUT request and return JSON response.

        Raises HttpRequestError on connection failure, timeout, or HTTP error.
        """
        ...

    @abstractmethod
    async def aclose(self) -> None:
        """Close the underlying client. Call on application shutdown."""
        ...
