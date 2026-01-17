from abc import ABC, abstractmethod

from scruffy.domain.entities.media import Media
from scruffy.domain.value_objects.media_type import MediaType


class MediaRepositoryInterface(ABC):
    """Abstract interface for fetching media information."""

    @abstractmethod
    async def get_media(
        self, external_service_id: int, media_type: MediaType, seasons: list[int]
    ) -> Media:
        """Get media information by external service ID."""
        pass

    @abstractmethod
    async def delete_media(
        self, external_service_id: int, media_type: MediaType, seasons: list[int]
    ) -> None:
        """Delete media by external service ID."""
        pass
