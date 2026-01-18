from abc import ABC, abstractmethod

from scruffy.use_cases.dtos.media_info_dto import MediaInfoDTO


class NotificationServiceInterface(ABC):
    """Abstract interface for sending notifications."""

    @abstractmethod
    async def send_reminder_notice(
        self, user_email: str, media_dto: MediaInfoDTO, days_left: int
    ) -> None:
        """Send a reminder notification to the user."""
        pass

    @abstractmethod
    async def send_deletion_notice(
        self, user_email: str, media_dto: MediaInfoDTO
    ) -> None:
        """Send a deletion notification to the user."""
        pass
