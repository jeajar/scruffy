"""Use case for requesting a time extension on a media request."""

import asyncio
import logging

from scruffy.domain.value_objects.media_status import MediaStatus
from scruffy.use_cases.interfaces.extension_repository_interface import (
    ExtensionRepositoryInterface,
)
from scruffy.use_cases.interfaces.request_repository_interface import (
    RequestRepositoryInterface,
)

logger = logging.getLogger(__name__)


class RequestExtensionUseCase:
    """Orchestrates requesting an extension for a media request."""

    def __init__(
        self,
        extension_repository: ExtensionRepositoryInterface,
        request_repository: RequestRepositoryInterface,
    ):
        """Initialize with extension and request repositories."""
        self.extension_repository = extension_repository
        self.request_repository = request_repository
        logger.debug("Initialized RequestExtensionUseCase")

    async def execute(self, request_id: int, plex_user_id: int) -> bool:
        """
        Request an extension for a media request.

        Returns True if extension was recorded, False if already extended.
        Raises ValueError if request does not exist or is not available.
        """
        # Validate request exists in Overseerr
        request_dto = await self.request_repository.get_request(request_id)
        if request_dto is None:
            logger.warning(
                "Extension requested for non-existent request",
                extra={"request_id": request_id},
            )
            raise ValueError("Request not found")

        # Only allow extension for available or partially available media
        if request_dto.media_status not in [
            MediaStatus.AVAILABLE,
            MediaStatus.PARTIALLY_AVAILABLE,
        ]:
            logger.warning(
                "Extension requested for non-available media",
                extra={
                    "request_id": request_id,
                    "media_status": request_dto.media_status.name,
                },
            )
            raise ValueError("Media is not yet available for extension")

        # Record extension (returns False if already extended)
        return await asyncio.to_thread(
            self.extension_repository.extend_request,
            request_id,
            plex_user_id,
        )
