from scruffy.domain.entities.media import Media
from scruffy.domain.entities.media_request import MediaRequest
from scruffy.domain.value_objects.media_status import MediaStatus
from scruffy.use_cases.interfaces.media_repository_interface import (
    MediaRepositoryInterface,
)
from scruffy.use_cases.interfaces.request_repository_interface import (
    RequestRepositoryInterface,
)


class CheckMediaRequestsUseCase:
    """Orchestrates checking all media requests."""

    def __init__(
        self,
        request_repository: RequestRepositoryInterface,
        media_repository: MediaRepositoryInterface,
    ):
        """Initialize with required repositories."""
        self.request_repository = request_repository
        self.media_repository = media_repository

    async def execute(self) -> list[tuple[MediaRequest, Media]]:
        """Check all media requests and return those needing attention."""
        requests = await self.request_repository.get_requests()

        # Filter to only available or partially available requests
        to_check = [
            req
            for req in requests
            if req.media_status
            in [MediaStatus.PARTIALLY_AVAILABLE, MediaStatus.AVAILABLE]
        ]

        result = []
        for req in to_check:
            media = await self.media_repository.get_media(
                req.external_service_id, req.media_type, req.seasons
            )
            if media.is_available():
                result.append((req, media))

        return result
