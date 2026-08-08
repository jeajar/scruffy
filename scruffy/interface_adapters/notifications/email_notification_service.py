from scruffy.interface_adapters.interfaces.email_client_interface import IEmailClient
from scruffy.use_cases.dtos.media_info_dto import MediaInfoDTO
from scruffy.use_cases.interfaces.notification_service_interface import (
    NotificationServiceInterface,
)


class EmailNotificationService(NotificationServiceInterface):
    """Email notification service implementing NotificationServiceInterface."""

    def __init__(self, email_client: IEmailClient):
        """Initialize with email client."""
        self.email_client = email_client

    async def send_reminder_notice(
        self,
        user_email: str,
        media_dto: MediaInfoDTO,
        days_left: int,
        request_id: int,
    ) -> None:
        """Send a reminder notification to the user."""
        await self.email_client.send_reminder_notice(
            user_email, media_dto.title, media_dto.poster, days_left, request_id
        )

    async def send_deletion_notice(
        self, user_email: str, media_dto: MediaInfoDTO
    ) -> None:
        """Send a deletion notification to the user."""
        await self.email_client.send_deletion_notice(
            user_email, media_dto.title, media_dto.poster, days_left=0
        )
