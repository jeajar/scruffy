from abc import ABC, abstractmethod
from typing import Any

from scruffy.infra.data_transfer_objects import RequestDTO


class IMediaRequestRepository(ABC):
    """Abstract interface for media request repositories."""

    @abstractmethod
    async def status(self) -> bool:
        """Check if the repository connection is working."""

    @abstractmethod
    async def get_requests(
        self, limit: int = 100, offset: int = 0, status_filter: str | None = None
    ) -> list[RequestDTO]:
        """Retrieve media requests."""

    @abstractmethod
    async def delete_request(self, request_id: int) -> None:
        """Delete a request by its ID."""

    @abstractmethod
    async def delete_media(self, media_id: int) -> None:
        """Delete media by its ID."""

    @abstractmethod
    async def get_media_info(self, media_id: int) -> dict[str, Any]:
        """Get detailed information about media."""

    @abstractmethod
    async def get_request_count(self, status: str | None = None) -> int:
        """Get the total count of requests."""

    @abstractmethod
    async def get_settings(self) -> dict[str, Any]:
        """Get repository settings."""
