from scruffy.domain.value_objects.media_status import MediaStatus
from scruffy.frameworks_and_drivers.http.http_client import HttpClient
from scruffy.use_cases.dtos.request_dto import RequestDTO
from scruffy.use_cases.interfaces.request_repository_interface import (
    RequestRepositoryInterface,
)


class OverseerGateway(RequestRepositoryInterface):
    """Adapter for Overseerr API."""

    def __init__(self, base_url: str, api_key: str, http_client: HttpClient | None = None):
        """Initialize Overseerr gateway with base URL and API key."""
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.headers = {"X-Api-Key": api_key, "Accept": "application/json"}
        self.http_client = http_client or HttpClient()

    async def status(self) -> bool:
        """Test Overseerr connection status."""
        try:
            await self.http_client.get(
                f"{self.base_url}/api/v1/status", headers=self.headers
            )
            return True
        except Exception:
            return False

    async def get_requests(
        self, status_filter: MediaStatus | None = None
    ) -> list[RequestDTO]:
        """Fetch all media requests from Overseerr using pagination."""
        # Note: Overseerr API doesn't support filtering by MediaStatus directly
        # Filtering is done in the use case layer
        total_requests = await self.get_request_count()
        all_requests = []
        take = 100
        skip = 0

        while skip < total_requests:
            params = {"take": take, "skip": skip}

            response = await self.http_client.get(
                f"{self.base_url}/api/v1/request",
                headers=self.headers,
                params=params,
            )

            page_results = [
                RequestDTO.from_overseer_response(req)
                for req in response.get("results", [])
            ]
            all_requests.extend(page_results)

            if len(page_results) < take:
                break

            skip += take

        return all_requests

    async def delete_request(self, request_id: int) -> None:
        """Delete a request by its ID."""
        await self.http_client.delete(
            f"{self.base_url}/api/v1/request/{request_id}", headers=self.headers
        )

    async def delete_media(self, media_id: int) -> None:
        """Delete media by its ID."""
        await self.http_client.delete(
            f"{self.base_url}/api/v1/media/{media_id}", headers=self.headers
        )

    async def get_request_count(self) -> int:
        """Get total number of requests."""
        response = await self.http_client.get(
            f"{self.base_url}/api/v1/request/count",
            headers=self.headers,
        )
        return response["total"]
