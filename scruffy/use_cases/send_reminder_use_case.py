from scruffy.domain.entities.media import Media
from scruffy.domain.entities.media_request import MediaRequest
from scruffy.use_cases.interfaces.notification_service_interface import (
    NotificationServiceInterface,
)
from scruffy.use_cases.interfaces.reminder_repository_interface import (
    ReminderRepositoryInterface,
)


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

    async def execute(
        self, request: MediaRequest, media: Media, days_left: int
    ) -> None:
        """Send reminder if not already sent."""
        if not self.reminder_repository.has_reminder(request.request_id):
            await self.notification_service.send_reminder_notice(
                request.user_email, media, days_left
            )
            self.reminder_repository.add_reminder(request.request_id, request.user_id)
