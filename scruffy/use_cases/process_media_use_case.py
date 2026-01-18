"""Main orchestration use case for processing media requests."""

import logging

from scruffy.domain.services.retention_calculator import (
    RetentionCalculator,
    RetentionResult,
)
from scruffy.domain.value_objects.retention_policy import RetentionPolicy
from scruffy.use_cases.check_media_requests_use_case import CheckMediaRequestsUseCase
from scruffy.use_cases.delete_media_use_case import DeleteMediaUseCase
from scruffy.use_cases.send_reminder_use_case import SendReminderUseCase

logger = logging.getLogger(__name__)


class ProcessMediaUseCase:
    """Main orchestration use case for processing media."""

    def __init__(
        self,
        check_use_case: CheckMediaRequestsUseCase,
        send_reminder_use_case: SendReminderUseCase,
        delete_media_use_case: DeleteMediaUseCase,
        retention_policy: RetentionPolicy,
    ):
        """Initialize with required use cases and policy."""
        self.check_use_case = check_use_case
        self.send_reminder_use_case = send_reminder_use_case
        self.delete_media_use_case = delete_media_use_case
        self.retention_calculator = RetentionCalculator(retention_policy)
        logger.debug(
            "Initialized ProcessMediaUseCase",
            extra={
                "retention_days": retention_policy.retention_days,
                "reminder_days": retention_policy.reminder_days,
            },
        )

    async def execute(self) -> None:
        """Process all media requests and take appropriate actions."""
        logger.info("Starting media processing")
        results = await self.check_use_case.execute()
        logger.info(
            "Found media requests to process",
            extra={"request_count": len(results)},
        )

        reminders_sent = 0
        deletions_made = 0

        for request, media in results:
            retention_result = self.retention_calculator.evaluate(media)
            action_taken = await self._handle_result(request, media, retention_result)
            if action_taken == "reminder":
                reminders_sent += 1
            elif action_taken == "deletion":
                deletions_made += 1

        logger.info(
            "Media processing completed",
            extra={
                "total_processed": len(results),
                "reminders_sent": reminders_sent,
                "deletions_made": deletions_made,
            },
        )

    async def _handle_result(
        self, request, media, retention_result: RetentionResult
    ) -> str | None:
        """Handle individual media result. Returns action taken."""
        action = None

        if retention_result.remind:
            logger.info(
                "Sending reminder for media",
                extra={
                    "request_id": request.request_id,
                    "media_title": media.title,
                    "days_left": retention_result.days_left,
                    "user_email": request.user_email,
                },
            )
            await self.send_reminder_use_case.execute(
                request, media, retention_result.days_left
            )
            action = "reminder"

        if retention_result.delete:
            logger.info(
                "Deleting media",
                extra={
                    "request_id": request.request_id,
                    "media_title": media.title,
                    "user_email": request.user_email,
                },
            )
            await self.delete_media_use_case.execute(request, media)
            action = "deletion"

        return action
