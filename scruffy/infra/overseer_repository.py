import httpx

from scruffy.infra.data_transfer_objects import RequestDTO


class OverseerRepository:
    def __init__(self, base_url: str, api_key: str):
        """Initialize Overseerr repository with base URL and API key."""
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.headers = {"X-Api-Key": api_key, "Accept": "application/json"}

    async def status(self) -> bool:
        """
        Test Overseerr connection status.
        Returns True if the connection is successful, False otherwise.
        """
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
    ) -> list[RequestDTO]:
        """Fetch all media requests from Overseerr using pagination.

        Args:
            take: Number of items per page (default 100)
            skip: Starting offset (default 0)
            filter_status: Optional status filter

        Returns:
            List of all RequestDTO objects
        """
        total_requests = await self.get_request_count(filter_status)
        all_requests = []

        while skip < total_requests:
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

                page_results = [
                    RequestDTO.from_overseer_response(req)
                    for req in response.json().get("results", [])
                ]
                all_requests.extend(page_results)

                if len(page_results) < take:
                    break

                skip += take

        return all_requests

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

    async def get_media_info(self, media_id: int) -> dict:
        """Fetch detailed media information."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/media/{media_id}", headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    async def get_request_count(self, status: str | None = None) -> int:
        """Get total number of requests."""
        async with httpx.AsyncClient() as client:
            params = {"filter": status} if status else {}
            response = await client.get(
                f"{self.base_url}/api/v1/request/count",
                headers=self.headers,
                params=params,
            )
            response.raise_for_status()
            return response.json()["total"]

    async def get_main_settings(self) -> dict:
        """Get main settings from Overseerr."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/settings/main", headers=self.headers
            )
            response.raise_for_status()
            return response.json()
