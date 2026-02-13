"""Main orchestration use case for processing media requests."""

import asyncio
import logging
from collections.abc import Callable

from scruffy.domain.services.retention_calculator import (
    RetentionCalculator,
    RetentionResult,
)
from scruffy.domain.value_objects.retention_policy import RetentionPolicy
from scruffy.use_cases.check_media_requests_use_case import CheckMediaRequestsUseCase
from scruffy.use_cases.delete_media_use_case import DeleteMediaUseCase
from scruffy.use_cases.mappers import map_media_dto_to_entity, map_request_dto_to_entity
from scruffy.use_cases.send_reminder_use_case import SendReminderUseCase

logger = logging.getLogger(__name__)


class ProcessMediaUseCase:
    """Main orchestration use case for processing media."""

    def __init__(
        self,
        check_use_case: CheckMediaRequestsUseCase,
        send_reminder_use_case: SendReminderUseCase,
        delete_media_use_case: DeleteMediaUseCase,
        retention_policy_or_provider: RetentionPolicy | Callable[[], RetentionPolicy],
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
        """Process all media requests and take appropriate actions.

        Returns summary dict with:
        - reminders_sent: items for which an email was actually sent this run
        - needs_attention: items below reminder threshold but already reminded (no email this run)
        - deletions: items that were deleted
        """
        logger.info("Starting media processing")
        results = await self.check_use_case.execute_with_retention(
            self.retention_calculator
        )
        logger.info(
            "Found media requests to process",
            extra={"request_count": len(results)},
        )

        reminders_sent_summary: list[dict] = []
        needs_attention_summary: list[dict] = []
        deletions_summary: list[dict] = []

        # Filter to results needing remind or delete (extension-aware retention from execute_with_retention)
        to_handle = []
        for result in results:
            if result.retention.remind or result.retention.delete:
                request = map_request_dto_to_entity(result.request)
                media = map_media_dto_to_entity(result.media)
                retention_result = RetentionResult(
                    remind=result.retention.remind,
                    delete=result.retention.delete,
                    days_left=result.retention.days_left,
                )
                to_handle.append(
                    (request, media, retention_result, result.retention.reminder_sent)
                )

        # Run all remind/delete actions in parallel
        if to_handle:
            outcomes = await asyncio.gather(
                *[
                    self._handle_result(req, med, ret, reminder_sent)
                    for req, med, ret, reminder_sent in to_handle
                ],
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
                    for entry in entries:
                        kind = entry.get("kind", "deletion")
                        if kind == "reminders_sent":
                            reminders_sent_summary.append(entry)
                        elif kind == "needs_attention":
                            needs_attention_summary.append(entry)
                        else:
                            deletions_summary.append(entry)

        logger.info(
            "Media processing completed",
            extra={
                "total_processed": len(results),
                "reminders_sent": len(reminders_sent_summary),
                "needs_attention": len(needs_attention_summary),
                "deletions_made": len(deletions_summary),
            },
        )

        return {
            "reminders_sent": reminders_sent_summary,
            "needs_attention": needs_attention_summary,
            "deletions": deletions_summary,
        }

    async def _handle_result(
        self,
        request,
        media,
        retention_result: RetentionResult,
        reminder_already_sent: bool,
    ) -> tuple[str | None, list[dict]]:
        """Handle individual media result. Returns (action, list of summary entries)."""
        action = None
        summary_entries: list[dict] = []

        if retention_result.remind:
            logger.info(
                "Processing reminder for media",
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
            base = {
                "email": request.user_email,
                "title": media.title,
                "days_left": retention_result.days_left,
            }
            if reminder_already_sent:
                summary_entries.append({"kind": "needs_attention", **base})
            else:
                summary_entries.append({"kind": "reminders_sent", **base})

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
            summary_entries.append(
                {
                    "kind": "deletion",
                    "email": request.user_email,
                    "title": media.title,
                }
            )

        return (action, summary_entries)
