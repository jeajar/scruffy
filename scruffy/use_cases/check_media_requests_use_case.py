"""Use case for checking media requests and their status."""

import asyncio
import logging

from scruffy.domain.entities.media import Media
from scruffy.domain.entities.media_request import MediaRequest
from scruffy.domain.services.retention_calculator import RetentionCalculator
from scruffy.domain.value_objects.media_status import MediaStatus
from scruffy.use_cases.dtos.media_check_result_dto import (
    MediaCheckResultDTO,
    RetentionResultDTO,
)
from scruffy.use_cases.interfaces.extension_repository_interface import (
    ExtensionRepositoryInterface,
)
from scruffy.use_cases.interfaces.media_repository_interface import (
    MediaRepositoryInterface,
)
from scruffy.use_cases.interfaces.request_repository_interface import (
    RequestRepositoryInterface,
)
from scruffy.use_cases.mappers import map_media_dto_to_entity, map_request_dto_to_entity

logger = logging.getLogger(__name__)


class CheckMediaRequestsUseCase:
    """Orchestrates checking all media requests."""

    def __init__(
        self,
        request_repository: RequestRepositoryInterface,
        media_repository: MediaRepositoryInterface,
        extension_repository: ExtensionRepositoryInterface | None = None,
    ):
        """Initialize with required repositories."""
        self.request_repository = request_repository
        self.media_repository = media_repository
        self.extension_repository = extension_repository
        logger.debug("Initialized CheckMediaRequestsUseCase")

    async def execute(self) -> list[tuple[MediaRequest, Media]]:
        """Check all media requests and return those needing attention."""
        logger.info("Checking media requests")
        request_dtos = await self.request_repository.get_requests()
        logger.debug(
            "Retrieved requests from repository",
            extra={"total_requests": len(request_dtos)},
        )

        # Convert DTOs to entities
        requests = [map_request_dto_to_entity(dto) for dto in request_dtos]

        # Filter to only available or partially available requests
        to_check = [
            req
            for req in requests
            if req.media_status
            in [MediaStatus.PARTIALLY_AVAILABLE, MediaStatus.AVAILABLE]
        ]
        logger.info(
            "Filtered to available requests",
            extra={
                "total_requests": len(requests),
                "available_requests": len(to_check),
            },
        )

        coros = [
            self.media_repository.get_media(
                req.external_service_id, req.media_type, req.seasons
            )
            for req in to_check
        ]
        gathered = await asyncio.gather(*coros, return_exceptions=True)

        result = []
        for req, outcome in zip(to_check, gathered, strict=False):
            if isinstance(outcome, Exception):
                logger.error(
                    "Failed to fetch media info",
                    extra={
                        "request_id": req.request_id,
                        "external_service_id": req.external_service_id,
                        "error": str(outcome),
                    },
                )
                continue
            media_dto = outcome
            media = map_media_dto_to_entity(media_dto)
            if media.is_available():
                result.append((req, media))
                logger.debug(
                    "Media is available",
                    extra={
                        "request_id": req.request_id,
                        "title": media.title,
                        "available_since": str(media.available_since),
                    },
                )

        logger.info(
            "Completed media request check",
            extra={"requests_needing_attention": len(result)},
        )
        return result

    async def execute_with_retention(
        self, retention_calculator: RetentionCalculator
    ) -> list[MediaCheckResultDTO]:
        """Check all media requests and return DTOs with retention information."""
        logger.info("Checking media requests with retention info")
        request_dtos = await self.request_repository.get_requests()

        # Get extended request IDs and extension_days for retention calculation
        extended_ids: set[int] = set()
        extension_days = 0
        if self.extension_repository is not None:
            extended_ids, extension_days = await asyncio.gather(
                asyncio.to_thread(
                    self.extension_repository.get_extended_request_ids
                ),
                asyncio.to_thread(
                    self.extension_repository.get_extension_days
                ),
            )

        # Convert DTOs to entities for business logic
        requests = [map_request_dto_to_entity(dto) for dto in request_dtos]

        # Filter to only available or partially available requests
        to_check = [
            req
            for req in requests
            if req.media_status
            in [MediaStatus.PARTIALLY_AVAILABLE, MediaStatus.AVAILABLE]
        ]
        logger.debug(
            "Filtered requests for retention check",
            extra={"to_check": len(to_check)},
        )

        coros = [
            self.media_repository.get_media(
                req.external_service_id, req.media_type, req.seasons
            )
            for req in to_check
        ]
        gathered = await asyncio.gather(*coros, return_exceptions=True)

        result = []
        for req, outcome in zip(to_check, gathered, strict=False):
            if isinstance(outcome, Exception):
                logger.error(
                    "Failed to process media for retention",
                    extra={
                        "request_id": req.request_id,
                        "error": str(outcome),
                    },
                )
                continue
            media_dto = outcome
            media = map_media_dto_to_entity(media_dto)
            if media.is_available():
                is_extended = req.request_id in extended_ids
                ext_days = extension_days if is_extended else 0
                retention_result = retention_calculator.evaluate(
                    media, extension_days=ext_days
                )
                retention_dto = RetentionResultDTO(
                    remind=retention_result.remind,
                    delete=retention_result.delete,
                    days_left=retention_result.days_left,
                    extended=is_extended,
                )
                request_dto = next(
                    dto for dto in request_dtos if dto.request_id == req.request_id
                )
                result.append(
                    MediaCheckResultDTO(
                        request=request_dto, media=media_dto, retention=retention_dto
                    )
                )
                logger.debug(
                    "Evaluated retention for media",
                    extra={
                        "request_id": req.request_id,
                        "title": media.title,
                        "days_left": retention_result.days_left,
                        "remind": retention_result.remind,
                        "delete": retention_result.delete,
                        "extended": is_extended,
                    },
                )

        logger.info(
            "Completed retention check",
            extra={"results_count": len(result)},
        )
        return result
