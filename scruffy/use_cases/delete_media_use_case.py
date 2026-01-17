from scruffy.domain.entities.media import Media
from scruffy.domain.entities.media_request import MediaRequest
from scruffy.use_cases.interfaces.media_repository_interface import (
    MediaRepositoryInterface,
)
from scruffy.use_cases.interfaces.notification_service_interface import (
    NotificationServiceInterface,
)
from scruffy.use_cases.interfaces.request_repository_interface import (
    RequestRepositoryInterface,
)
from scruffy.use_cases.mappers import map_media_entity_to_dto


class DeleteMediaUseCase:
    """Handles media deletion."""

    def __init__(
        self,
        media_repository: MediaRepositoryInterface,
        request_repository: RequestRepositoryInterface,
        notification_service: NotificationServiceInterface,
    ):
        """Initialize with required dependencies."""
        self.media_repository = media_repository
        self.request_repository = request_repository
        self.notification_service = notification_service

    async def execute(self, request: MediaRequest, media: Media) -> None:
        """Delete media and send notification."""
        # Delete from media service (Radarr/Sonarr)
        await self.media_repository.delete_media(
            request.external_service_id, request.media_type, request.seasons
        )

        # Delete from Overseerr
        await self.request_repository.delete_request(request.request_id)
        await self.request_repository.delete_media(request.media_id)

        # Convert entity to DTO for notification service
        media_dto = map_media_entity_to_dto(media)
        await self.notification_service.send_deletion_notice(
            request.user_email, media_dto
        )
