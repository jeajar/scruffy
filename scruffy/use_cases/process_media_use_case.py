"""Main orchestration use case for processing media requests."""

import asyncio
import logging
from typing import Callable, Union

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
        retention_policy_or_provider: Union[
            RetentionPolicy, Callable[[], RetentionPolicy]
        ],
    ):
        """Initialize with required use cases and policy (or policy provider)."""
        self.check_use_case = check_use_case
        self.send_reminder_use_case = send_reminder_use_case
        self.delete_media_use_case = delete_media_use_case
        self.retention_calculator = RetentionCalculator(retention_policy_or_provider)
        policy = (
            retention_policy_or_provider()
            if callable(retention_policy_or_provider)
            else retention_policy_or_provider
        )
        logger.debug(
            "Initialized ProcessMediaUseCase",
            extra={
                "retention_days": policy.retention_days,
                "reminder_days": policy.reminder_days,
            },
        )

    async def execute(self) -> dict:
        """Process all media requests and take appropriate actions. Returns summary dict with 'reminders' and 'deletions' lists."""
        logger.info("Starting media processing")
        results = await self.check_use_case.execute()
        logger.info(
            "Found media requests to process",
            extra={"request_count": len(results)},
        )

        reminders_summary: list[dict] = []
        deletions_summary: list[dict] = []

        # Build list of (request, media, retention_result) that need an action
        to_handle = []
        for request, media in results:
            retention_result = self.retention_calculator.evaluate(media)
            if retention_result.remind or retention_result.delete:
                to_handle.append((request, media, retention_result))

        # Run all remind/delete actions in parallel
        if to_handle:
            outcomes = await asyncio.gather(
                *[self._handle_result(req, med, ret) for req, med, ret in to_handle],
                return_exceptions=True,
            )
            for outcome in outcomes:
                if isinstance(outcome, Exception):
                    logger.error(
                        "Process media action failed",
                        extra={"error": str(outcome)},
                    )
                elif isinstance(outcome, tuple):
                    _action, entries = outcome
                    if entries:
                        for entry in entries:
                            if "days_left" in entry:
                                reminders_summary.append(entry)
                            else:
                                deletions_summary.append(entry)
        else:
            pass

        logger.info(
            "Media processing completed",
            extra={
                "total_processed": len(results),
                "reminders_sent": len(reminders_summary),
                "deletions_made": len(deletions_summary),
            },
        )

        return {
            "reminders": reminders_summary,
            "deletions": deletions_summary,
        }

    async def _handle_result(
        self, request, media, retention_result: RetentionResult
    ) -> tuple[str | None, list[dict]]:
        """Handle individual media result. Returns (action, list of summary entries)."""
        action = None
        summary_entries: list[dict] = []

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
            summary_entries.append({
                "email": request.user_email,
                "title": media.title,
                "days_left": retention_result.days_left,
            })

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
            summary_entries.append({
                "email": request.user_email,
                "title": media.title,
            })

        return (action, summary_entries)
