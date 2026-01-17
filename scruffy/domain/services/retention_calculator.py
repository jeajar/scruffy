from dataclasses import dataclass

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

    def evaluate(self, media: Media) -> RetentionResult:
        """Evaluate retention policy for media."""
        if not media.is_available():
            return RetentionResult(remind=False, delete=False, days_left=0)

        remind = self.policy.should_remind(media.available_since)
        delete = self.policy.should_delete(media.available_since)
        days_left = self.policy.days_remaining(media.available_since)

        return RetentionResult(remind=remind, delete=delete, days_left=days_left)
