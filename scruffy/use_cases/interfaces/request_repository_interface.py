from abc import ABC, abstractmethod

from scruffy.domain.value_objects.media_status import MediaStatus
from scruffy.use_cases.dtos.request_dto import RequestDTO


class RequestRepositoryInterface(ABC):
    """Abstract interface for managing media requests."""

    @abstractmethod
    async def get_requests(
        self, status_filter: MediaStatus | None = None
    ) -> list[RequestDTO]:
        """Get all media requests, optionally filtered by status."""
        pass

    @abstractmethod
    async def delete_request(self, request_id: int) -> None:
        """Delete a request by its ID."""
        pass

    @abstractmethod
    async def delete_media(self, media_id: int) -> None:
        """Delete media by its ID."""
        pass

    @abstractmethod
    async def status(self) -> bool:
        """Check if the repository connection is valid."""
        pass
