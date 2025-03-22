from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class MediaClientProtocol(Protocol):
    """Protocol defining the contract for media API clients."""

    async def check_status(self) -> bool:
        """Check if the API is accessible."""
        ...

    async def get_requests(
        self, take: int, skip: int, filter_status: str | None
    ) -> dict[str, Any]:
        """Fetch media requests."""
        ...

    async def delete_request(self, request_id: int) -> None:
        """Delete a request by its ID."""
        ...

    async def delete_media(self, media_id: int) -> None:
        """Delete media objects in the Request system by its ID."""
        ...

    async def get_media_info(self, media_id: int) -> dict[str, Any]:
        """Fetch detailed media information."""
        ...

    async def get_request_count(self, status: str | None) -> dict[str, Any]:
        """Get total number of requests."""
        ...

    async def get_main_settings(self) -> dict[str, Any]:
        """Get main settings from the API."""
        ...
