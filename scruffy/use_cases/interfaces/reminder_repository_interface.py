from abc import ABC, abstractmethod


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

    @abstractmethod
    def get_request_ids_with_reminders(self, request_ids: list[int]) -> set[int]:
        """Return set of request_ids that have reminder records."""
        pass
