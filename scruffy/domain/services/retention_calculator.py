from dataclasses import dataclass
from datetime import timedelta

from scruffy.domain.entities.media import Media
from scruffy.domain.value_objects.retention_policy import RetentionPolicy


@dataclass(frozen=True)
class RetentionResult:
    """Result of retention policy evaluation."""

    remind: bool
    delete: bool
    days_left: int = 0


class RetentionCalculator:
    """Pure domain service for calculating retention decisions."""

    def __init__(self, policy: RetentionPolicy):
        """Initialize with retention policy."""
        self.policy = policy

    def evaluate(
        self, media: Media, extension_days: int = 0
    ) -> RetentionResult:
        """
        Evaluate retention policy for media.

        When extension_days > 0, treats effective_available_since as
        available_since + extension_days (pushes the clock back).
        """
        if not media.is_available():
            return RetentionResult(remind=False, delete=False, days_left=0)

        available_since = media.available_since
        if extension_days > 0 and available_since is not None:
            available_since = available_since + timedelta(days=extension_days)

        remind = self.policy.should_remind(available_since)
        delete = self.policy.should_delete(available_since)
        days_left = self.policy.days_remaining(available_since)

        return RetentionResult(remind=remind, delete=delete, days_left=days_left)
