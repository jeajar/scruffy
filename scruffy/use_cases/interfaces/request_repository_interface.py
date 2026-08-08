from abc import ABC, abstractmethod

from scruffy.use_cases.dtos.request_dto import RequestDTO


class RequestRepositoryInterface(ABC):
    """Abstract interface for managing media requests."""

    @abstractmethod
    async def get_request(self, request_id: int) -> RequestDTO | None:
        """Get a single request by ID. Returns None if not found."""
        pass

    @abstractmethod
    async def get_requests(self) -> list[RequestDTO]:
        """Get all media requests. Filtering by status happens in the use case layer."""
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
