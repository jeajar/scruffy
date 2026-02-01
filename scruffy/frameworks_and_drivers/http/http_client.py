from typing import Any

import httpx


class HttpClient:
    """Wrapper around httpx for making HTTP requests with connection pooling."""

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
        response = await self._client.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

    async def delete(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
    ) -> None:
        """Make DELETE request."""
        response = await self._client.delete(url, headers=headers, params=params)
        response.raise_for_status()

    async def put(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make PUT request and return JSON response."""
        response = await self._client.put(url, headers=headers, json=json)
        response.raise_for_status()
        return response.json()

    async def aclose(self) -> None:
        """Close the underlying HTTP client. Call on application shutdown."""
        await self._client.aclose()
