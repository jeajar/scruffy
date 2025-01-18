import asyncio
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import List, Tuple

from scruffy.infra import (
    MediaInfoDTO,
    MediaStatus,
    OverseerRepository,
    RadarrRepository,
    RequestDTO,
    SonarrRepository,
)
from scruffy.logging import setup_logger
from scruffy.services import EmailService
from scruffy.settings import settings


@dataclass(frozen=True)
class Result:
    remind: bool
    delete: bool


class MediaManager:
    def __init__(
        self,
        overseer: OverseerRepository,
        sonarr: SonarrRepository,
        radarr: RadarrRepository,
        email_service: EmailService,
    ):
        self.overseer = overseer
        self.sonarr = sonarr
        self.radarr = radarr
        self.email_service = email_service
        self.logger = setup_logger(__class__.__name__, settings.log_level)

    async def check_requests(self) -> List[Tuple[RequestDTO, MediaInfoDTO]]:
        """Check all media requests and return those needing attention."""
        self.logger.info("Checking media requests from Overseerr")
        requests = await self.overseer.get_requests()

        to_check = [
            req
            for req in requests
            if req.media_status
            in [MediaStatus.PARTIALLY_AVAILABLE, MediaStatus.AVAILABLE]
        ]

        self.logger.info(f"Found {len(to_check)} available media requests to check")
        result = []
        for req in to_check:
            media_info = await self._get_media_info(req)
            self.logger.debug("Got media info: %s", asdict(media_info))
            result.append((req, media_info))

        return result

    async def _get_media_info(self, request: RequestDTO) -> MediaInfoDTO:
        """Get media info from appropriate service."""
        if request.type == "movie":
            return await self.radarr.get_movie(request.external_service_id)
        return await self.sonarr.get_series_info(
            request.external_service_id, request.seasons
        )

    def _check_retention_policy(
        self, request: RequestDTO, media_info: MediaInfoDTO
    ) -> Result:
        """Apply retention policy to media."""
        if not media_info.available:
            return Result(remind=False, delete=False)

        age: int = datetime.now(media_info.available_since.tzinfo) - request.updated_at
        remind: bool = settings.retention_days - age.days == settings.reminder_days
        delete: bool = age.days >= settings.retention_days

        return Result(remind=remind, delete=delete)

    async def process_media(self) -> None:
        """Process all media requests and take appropriate actions."""
        self.logger.info("Processing media requests")
        results = await self.check_requests()

        for request, media_info in results:
            result = self._check_retention_policy(request, media_info)
            if result.remind:
                self.logger.info(
                    "Sending reminder to %s for %s",
                    request.user_email,
                    media_info.title,
                )
            if result.delete:
                self.logger.info(
                    "Deleting %s and notify %s", media_info.title, request.user_email
                )
            await self._handle_result(request, media_info, result)

    async def _handle_result(
        self, request: RequestDTO, media_info: MediaInfoDTO, result: Result
    ) -> None:
        """Handle individual media result."""
        if result.remind:
            days_left = (
                settings.retention_days
                - (
                    datetime.now(media_info.available_since.tzinfo) - request.updated_at
                ).days
            )
            await self.email_service.send_reminder_notice(
                request.user_email, media_info, days_left
            )

        if result.delete:
            await self._delete_media(request)
            await self.overseer.delete_request(request.request_id)
            await self.email_service.send_deletion_notice(
                request.user_email, media_info
            )

    async def _delete_media(self, request: RequestDTO) -> None:
        """Delete media from appropriate service."""
        if request.type == "movie":
            await self.radarr.delete_movie(request.external_service_id)
        else:
            await self.sonarr.delete_series_seasons(
                request.external_service_id, request.seasons
            )


if __name__ == "__main__":
    manager = MediaManager(
        overseer=OverseerRepository(
            str(settings.overseerr_url), settings.overseerr_api_key
        ),
        sonarr=SonarrRepository(str(settings.sonarr_url), settings.sonarr_api_key),
        radarr=RadarrRepository(str(settings.radarr_url), settings.radarr_api_key),
        email_service=EmailService(),
    )

    asyncio.run(manager.process_media())
