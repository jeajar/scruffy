from abc import ABC, abstractmethod

from scruffy.domain.value_objects.media_type import MediaType
from scruffy.interface_adapters.dtos.media_info_dto import MediaInfoDTO


class MediaRepositoryInterface(ABC):
    """Abstract interface for fetching media information."""

    @abstractmethod
    async def get_media(
        self, external_service_id: int, media_type: MediaType, seasons: list[int]
    ) -> MediaInfoDTO:
        """Get media information by external service ID."""
        pass

    @abstractmethod
    async def delete_media(
        self, external_service_id: int, media_type: MediaType, seasons: list[int]
    ) -> None:
        """Delete media by external service ID."""
        pass
