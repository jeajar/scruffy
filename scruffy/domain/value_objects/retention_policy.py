from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
class RetentionPolicy:
    """Value object encapsulating retention policy rules."""

    retention_days: int
    reminder_days: int

    def should_remind(self, available_since: datetime | None) -> bool:
        """Check if a reminder should be sent."""
        if available_since is None:
            return False
        age = datetime.now(available_since.tzinfo) - available_since
        return self.retention_days - age.days <= self.reminder_days

    def should_delete(self, available_since: datetime | None) -> bool:
        """Check if media should be deleted."""
        if available_since is None:
            return False
        age = datetime.now(available_since.tzinfo) - available_since
        return age.days >= self.retention_days

    def days_remaining(self, available_since: datetime | None) -> int:
        """Calculate days remaining before deletion."""
        if available_since is None:
            return 0
        age = datetime.now(available_since.tzinfo) - available_since
        return self.retention_days - age.days
