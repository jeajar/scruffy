"""HTTP client implementation using httpx."""

from typing import Any

import httpx

from scruffy.interface_adapters.interfaces.http_client_interface import (
    HttpRequestError,
    IHttpClient,
)


class HttpClient(IHttpClient):
    """httpx-based implementation of HttpClientInterface."""

    def __init__(self, timeout: float = 30.0):
        """Initialize with a long-lived async client for connection reuse."""
        self._client = httpx.AsyncClient(timeout=timeout)

    async def get(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make GET request and return JSON response."""
        try:
            response = await self._client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            raise HttpRequestError(str(e)) from e

    async def delete(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
    ) -> None:
        """Make DELETE request."""
        try:
            response = await self._client.delete(url, headers=headers, params=params)
            response.raise_for_status()
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            raise HttpRequestError(str(e)) from e

    async def put(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make PUT request and return JSON response."""
        try:
            response = await self._client.put(url, headers=headers, json=json)
            response.raise_for_status()
            return response.json()
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            raise HttpRequestError(str(e)) from e

    async def aclose(self) -> None:
        """Close the underlying HTTP client. Call on application shutdown."""
        await self._client.aclose()
