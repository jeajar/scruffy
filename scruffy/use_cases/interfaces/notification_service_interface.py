from abc import ABC, abstractmethod

from scruffy.domain.entities.media import Media


class NotificationServiceInterface(ABC):
    """Abstract interface for sending notifications."""

    @abstractmethod
    async def send_reminder_notice(
        self, user_email: str, media: Media, days_left: int
    ) -> None:
        """Send a reminder notification to the user."""
        pass

    @abstractmethod
    async def send_deletion_notice(self, user_email: str, media: Media) -> None:
        """Send a deletion notification to the user."""
        pass
