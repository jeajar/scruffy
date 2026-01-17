from typing import Any

import httpx


class HttpClient:
    """Wrapper around httpx for making HTTP requests."""

    async def get(
        self, url: str, headers: dict[str, str] | None = None, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Make GET request and return JSON response."""
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()

    async def delete(
        self, url: str, headers: dict[str, str] | None = None, params: dict[str, Any] | None = None
    ) -> None:
        """Make DELETE request."""
        async with httpx.AsyncClient() as client:
            response = await client.delete(url, headers=headers, params=params)
            response.raise_for_status()

    async def put(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make PUT request and return JSON response."""
        async with httpx.AsyncClient() as client:
            response = await client.put(url, headers=headers, json=json)
            response.raise_for_status()
            return response.json()
