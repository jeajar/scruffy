from typing import Any

import httpx


class OverseerrClient:
    """HTTP client for interacting with the Overseerr API."""

    def __init__(self, base_url: str, api_key: str):
        """Initialize the Overseerr API client."""
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.headers = {"X-Api-Key": api_key, "Accept": "application/json"}

    async def check_status(self) -> bool:
        """Check if the Overseerr API is accessible."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/status", headers=self.headers
                )
                response.raise_for_status()
                return True
        except httpx.HTTPError:
            return False

    async def get_requests(
        self, take: int = 100, skip: int = 0, filter_status: str | None = None
    ) -> dict[str, Any]:
        """Fetch media requests from Overseerr."""
        async with httpx.AsyncClient() as client:
            params = {"take": take, "skip": skip}
            if filter_status:
                params["filter"] = filter_status

            response = await client.get(
                f"{self.base_url}/api/v1/request",
                headers=self.headers,
                params=params,
            )
            response.raise_for_status()
            return response.json()

    async def delete_request(self, request_id: int) -> None:
        """Delete a request by its ID."""
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base_url}/api/v1/request/{request_id}", headers=self.headers
            )
            response.raise_for_status()

    async def delete_media(self, media_id: int) -> None:
        """Delete media by its ID."""
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base_url}/api/v1/media/{media_id}", headers=self.headers
            )
            response.raise_for_status()

    async def get_media_info(self, media_id: int) -> dict[str, Any]:
        """Fetch detailed media information."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/media/{media_id}", headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    async def get_request_count(self, status: str | None = None) -> dict[str, Any]:
        """Get total number of requests."""
        async with httpx.AsyncClient() as client:
            params = {"filter": status} if status else {}
            response = await client.get(
                f"{self.base_url}/api/v1/request/count",
                headers=self.headers,
                params=params,
            )
            response.raise_for_status()
            return response.json()

    async def get_main_settings(self) -> dict[str, Any]:
        """Get main settings from Overseerr."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/settings/main", headers=self.headers
            )
            response.raise_for_status()
            return response.json()
