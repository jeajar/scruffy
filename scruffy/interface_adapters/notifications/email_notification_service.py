from scruffy.frameworks_and_drivers.email.email_client import EmailClient
from scruffy.interface_adapters.dtos.media_info_dto import MediaInfoDTO
from scruffy.use_cases.interfaces.notification_service_interface import (
    NotificationServiceInterface,
)


class EmailNotificationService(NotificationServiceInterface):
    """Email notification service implementing NotificationServiceInterface."""

    def __init__(self, email_client: EmailClient | None = None):
        """Initialize with email client."""
        self.email_client = email_client or EmailClient()

    async def send_reminder_notice(
        self, user_email: str, media_dto: MediaInfoDTO, days_left: int
    ) -> None:
        """Send a reminder notification to the user."""
        await self.email_client.send_reminder_notice(
            user_email, media_dto.title, media_dto.poster, days_left
        )

    async def send_deletion_notice(
        self, user_email: str, media_dto: MediaInfoDTO
    ) -> None:
        """Send a deletion notification to the user."""
        await self.email_client.send_deletion_notice(
            user_email, media_dto.title, media_dto.poster, days_left=0
        )
