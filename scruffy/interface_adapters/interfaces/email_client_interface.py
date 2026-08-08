"""Abstract email client interface for dependency inversion.

Implementations live in frameworks_and_drivers. EmailNotificationService depends
on this interface only, not on the concrete FastMail-based client.
"""

from abc import ABC, abstractmethod


class IEmailClient(ABC):
    """Abstract interface for sending transactional emails."""

    @abstractmethod
    async def send_deletion_notice(
        self, to_email: str, title: str, poster: str, days_left: int = 0
    ) -> None:
        """Send deletion notice email."""
        ...

    @abstractmethod
    async def send_reminder_notice(
        self,
        to_email: str,
        title: str,
        poster: str,
        days_left: int,
        request_id: int,
    ) -> None:
        """Send reminder notice email."""
        ...
