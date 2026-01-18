from scruffy.domain.entities.media import Media
from scruffy.domain.entities.media_request import MediaRequest
from scruffy.domain.services.retention_calculator import RetentionCalculator
from scruffy.domain.value_objects.media_status import MediaStatus
from scruffy.use_cases.dtos.media_check_result_dto import (
    MediaCheckResultDTO,
    RetentionResultDTO,
)
from scruffy.use_cases.interfaces.media_repository_interface import (
    MediaRepositoryInterface,
)
from scruffy.use_cases.interfaces.request_repository_interface import (
    RequestRepositoryInterface,
)
from scruffy.use_cases.mappers import map_media_dto_to_entity, map_request_dto_to_entity


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
        request_dtos = await self.request_repository.get_requests()

        # Convert DTOs to entities
        requests = [map_request_dto_to_entity(dto) for dto in request_dtos]

        # Filter to only available or partially available requests
        to_check = [
            req
            for req in requests
            if req.media_status
            in [MediaStatus.PARTIALLY_AVAILABLE, MediaStatus.AVAILABLE]
        ]

        result = []
        for req in to_check:
            media_dto = await self.media_repository.get_media(
                req.external_service_id, req.media_type, req.seasons
            )
            media = map_media_dto_to_entity(media_dto)
            if media.is_available():
                result.append((req, media))

        return result

    async def execute_with_retention(
        self, retention_calculator: RetentionCalculator
    ) -> list[MediaCheckResultDTO]:
        """Check all media requests and return DTOs with retention information."""
        request_dtos = await self.request_repository.get_requests()

        # Convert DTOs to entities for business logic
        requests = [map_request_dto_to_entity(dto) for dto in request_dtos]

        # Filter to only available or partially available requests
        to_check = [
            req
            for req in requests
            if req.media_status
            in [MediaStatus.PARTIALLY_AVAILABLE, MediaStatus.AVAILABLE]
        ]

        result = []
        for req in to_check:
            media_dto = await self.media_repository.get_media(
                req.external_service_id, req.media_type, req.seasons
            )
            media = map_media_dto_to_entity(media_dto)
            if media.is_available():
                retention_result = retention_calculator.evaluate(media)
                retention_dto = RetentionResultDTO(
                    remind=retention_result.remind,
                    delete=retention_result.delete,
                    days_left=retention_result.days_left,
                )
                # Find the original DTO for this request
                request_dto = next(
                    dto for dto in request_dtos if dto.request_id == req.request_id
                )
                result.append(
                    MediaCheckResultDTO(
                        request=request_dto, media=media_dto, retention=retention_dto
                    )
                )

        return result
