from abc import ABC, abstractmethod

from scruffy.domain.entities.reminder import Reminder


class ReminderRepositoryInterface(ABC):
    """Abstract interface for reminder persistence."""

    @abstractmethod
    def has_reminder(self, request_id: int) -> bool:
        """Check if a reminder has been sent for a request."""
        pass

    @abstractmethod
    def add_reminder(self, request_id: int, user_id: int) -> None:
        """Add a reminder record."""
        pass
