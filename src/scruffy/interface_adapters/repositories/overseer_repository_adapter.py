from typing import Any

from scruffy.app.interfaces.media_request_repository import IMediaRequestRepository

# TODO: move to app layer dtos ⬇️
from scruffy.infra.data_transfer_objects import RequestDTO
from scruffy.interface_adapters.protocols import MediaRequestClientProtocol


class OverseerRepositoryAdapter(IMediaRequestRepository):
    """Implementation of MediaRequestRepository for Overseerr."""

    def __init__(self, client: MediaRequestClientProtocol):
        """Initialize with an Overseerr API client."""
        self.client = client

    async def status(self) -> bool:
        """Check if the Overseerr API is accessible."""
        return await self.client.check_status()

    async def get_requests(
        self, limit: int = 100, offset: int = 0, status_filter: str | None = None
    ) -> list[RequestDTO]:
        """Get all media requests from Overseerr."""
        total_requests = await self.get_request_count(status_filter)
        all_requests = []
        current_offset = offset

        while current_offset < total_requests:
            response_data = await self.client.get_requests(
                limit, current_offset, status_filter
            )

            # Convert response data to DTOs and then to domain entities
            page_results = [
                RequestDTO.from_overseer_response(req).to_entity()
                for req in response_data.get("results", [])
            ]
            all_requests.extend(page_results)

            if len(page_results) < limit:
                break

            current_offset += limit

        return all_requests

    async def delete_request(self, request_id: int) -> None:
        """Delete a request by its ID."""
        await self.client.delete_request(request_id)

    async def delete_media(self, media_id: int) -> None:
        """Delete media by its ID."""
        await self.client.delete_media(media_id)

    async def get_media_info(self, media_id: int) -> dict[str, Any]:
        """Fetch detailed media information."""
        return await self.client.get_media_info(media_id)

    async def get_request_count(self, status: str | None = None) -> int:
        """Get total number of requests."""
        response = await self.client.get_request_count(status)
        return response.get("total", 0)

    async def get_settings(self) -> dict[str, Any]:
        """Get main settings from Overseerr."""
        return await self.client.get_main_settings()
