"""Use case for sending reminder notifications."""

import asyncio
import logging

from scruffy.domain.entities.media import Media
from scruffy.domain.entities.media_request import MediaRequest
from scruffy.use_cases.interfaces.notification_service_interface import (
    NotificationServiceInterface,
)
from scruffy.use_cases.interfaces.reminder_repository_interface import (
    ReminderRepositoryInterface,
)
from scruffy.use_cases.mappers import map_media_entity_to_dto

logger = logging.getLogger(__name__)


class SendReminderUseCase:
    """Handles sending reminder notifications."""

    def __init__(
        self,
        reminder_repository: ReminderRepositoryInterface,
        notification_service: NotificationServiceInterface,
    ):
        """Initialize with required dependencies."""
        self.reminder_repository = reminder_repository
        self.notification_service = notification_service
        logger.debug("Initialized SendReminderUseCase")

    async def execute(
        self, request: MediaRequest, media: Media, days_left: int
    ) -> None:
        """Send reminder if not already sent."""
        logger.debug(
            "Checking if reminder needed",
            extra={
                "request_id": request.request_id,
                "title": media.title,
                "days_left": days_left,
            },
        )

        has_reminder = await asyncio.to_thread(
            self.reminder_repository.has_reminder, request.request_id
        )
        if not has_reminder:
            logger.info(
                "Sending reminder notification",
                extra={
                    "request_id": request.request_id,
                    "title": media.title,
                    "user_email": request.user_email,
                    "days_left": days_left,
                },
            )
            # Convert entity to DTO for notification service
            media_dto = map_media_entity_to_dto(media)
            await self.notification_service.send_reminder_notice(
                request.user_email, media_dto, days_left, request.request_id
            )
            await asyncio.to_thread(
                self.reminder_repository.add_reminder,
                request.request_id,
                request.user_id,
            )
            logger.debug(
                "Reminder sent and recorded",
                extra={
                    "request_id": request.request_id,
                    "user_id": request.user_id,
                },
            )
        else:
            logger.debug(
                "Reminder already sent, skipping",
                extra={"request_id": request.request_id},
            )
