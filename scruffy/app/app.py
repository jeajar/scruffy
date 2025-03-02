import os
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Union

from scruffy.infra import (
    MediaInfoDTO,
    MediaStatus,
    OverseerRepository,
    RadarrRepository,
    ReminderRepository,
    RequestDTO,
    SonarrRepository,
)
from scruffy.logging import setup_logger
from scruffy.services import EmailService
from scruffy.settings import settings


@dataclass(frozen=True)
class RetentionResult:
    remind: bool
    delete: bool
    days_left: int = 0


class MediaManager:
    def __init__(
        self,
        overseer: OverseerRepository,
        sonarr: SonarrRepository,
        radarr: RadarrRepository,
        email_service: EmailService,
        reminder_repository: ReminderRepository,
    ):
        self.overseer = overseer
        self.sonarr = sonarr
        self.radarr = radarr
        self.email_service = email_service
        self.reminder_repository = reminder_repository
        self.logger = setup_logger(
            name=__class__.__name__,
            level=settings.log_level,
            log_file=self.log_file(),
        )

    def log_file(self) -> Union[str, None]:
        if os.access(settings.data_dir, os.W_OK):
            return str(Path(settings.data_dir).joinpath("scruffy.log"))
        return None

    async def validate_connections(self) -> bool:
        """
        Check all services are ready.
        Returns True if all services are ready, False otherwise.
        """
        valid = True
        for service in [self.overseer, self.sonarr, self.radarr]:
            if not await service.status():
                self.logger.error(
                    "Service %s connection failed", service.__class__.__name__
                )
                valid = False
        return valid

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
            if not media_info.available:
                self.logger.debug("Media not available: %s", asdict(media_info))
                continue
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
    ) -> RetentionResult:
        """Apply retention policy to media."""
        if not media_info.available:
            return RetentionResult(remind=False, delete=False)

        age: int = datetime.now(media_info.available_since.tzinfo) - request.updated_at
        remind: bool = settings.retention_days - age.days <= settings.reminder_days
        delete: bool = age.days >= settings.retention_days
        days_left: int = settings.retention_days - age.days

        return RetentionResult(remind=remind, delete=delete, days_left=days_left)

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
        self, request: RequestDTO, media_info: MediaInfoDTO, result: RetentionResult
    ) -> None:
        """Handle individual media result."""
        if result.remind:
            if not self.reminder_repository.has_reminder(request.request_id):
                await self.email_service.send_reminder_notice(
                    request.user_email, media_info, result.days_left
                )
                self.reminder_repository.add_reminder(
                    request.request_id, request.user_id
                )
                self.logger.info(
                    "Reminder sent for '%s' to '%s'",
                    media_info.title,
                    request.user_email,
                )
            else:
                self.logger.info(
                    "Reminder already sent for %s, skipping", media_info.title
                )

        if result.delete:
            await self._delete_media(request)
            self.logger.info("Deleted Media '%s' from service", request)
            await self.overseer.delete_request(request.request_id)
            await self.overseer.delete_media(request.media_id)
            self.logger.info("Deleted Overseer Request id: '%s'", request.request_id)

            await self.email_service.send_deletion_notice(
                request.user_email, media_info
            )
            self.logger.info(
                "Deletion notice sent for '%s' to '%s'",
                media_info.title,
                request.user_email,
            )

    async def _delete_media(self, request: RequestDTO) -> None:
        """Delete media from appropriate service."""
        if request.type == "movie":
            await self.radarr.delete_movie(request.external_service_id)
        else:
            await self.sonarr.delete_series_seasons(
                request.external_service_id, request.seasons
            )
