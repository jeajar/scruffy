from scruffy.domain.services.retention_calculator import (
    RetentionCalculator,
    RetentionResult,
)
from scruffy.domain.value_objects.retention_policy import RetentionPolicy
from scruffy.use_cases.check_media_requests_use_case import CheckMediaRequestsUseCase
from scruffy.use_cases.delete_media_use_case import DeleteMediaUseCase
from scruffy.use_cases.send_reminder_use_case import SendReminderUseCase


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

    async def execute(self) -> None:
        """Process all media requests and take appropriate actions."""
        results = await self.check_use_case.execute()

        for request, media in results:
            retention_result = self.retention_calculator.evaluate(media)
            await self._handle_result(request, media, retention_result)

    async def _handle_result(
        self, request, media, retention_result: RetentionResult
    ) -> None:
        """Handle individual media result."""
        if retention_result.remind:
            await self.send_reminder_use_case.execute(
                request, media, retention_result.days_left
            )

        if retention_result.delete:
            await self.delete_media_use_case.execute(request, media)
