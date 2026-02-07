from collections.abc import Callable
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


PolicyProvider = Callable[[], RetentionPolicy]


class RetentionCalculator:
    """Pure domain service for calculating retention decisions."""

    def __init__(
        self,
        policy_or_provider: RetentionPolicy | PolicyProvider,
    ):
        """
        Initialize with retention policy or policy provider.

        If policy_provider is a callable, it is invoked on each evaluate() to
        get the current policy (supports runtime config changes).
        """
        if callable(policy_or_provider) and not isinstance(
            policy_or_provider, RetentionPolicy
        ):
            self._policy_provider: PolicyProvider | None = policy_or_provider
            self._policy: RetentionPolicy | None = None
        else:
            self._policy_provider = None
            self._policy = policy_or_provider

    def _get_policy(self) -> RetentionPolicy:
        """Get current policy (from provider or fixed)."""
        if self._policy_provider is not None:
            return self._policy_provider()
        assert self._policy is not None
        return self._policy

    def evaluate(self, media: Media, extension_days: int = 0) -> RetentionResult:
        """
        Evaluate retention policy for media.

        When extension_days > 0, treats effective_available_since as
        available_since + extension_days (pushes the clock back).
        """
        if not media.is_available():
            return RetentionResult(remind=False, delete=False, days_left=0)

        policy = self._get_policy()
        available_since = media.available_since
        if extension_days > 0 and available_since is not None:
            available_since = available_since + timedelta(days=extension_days)

        remind = policy.should_remind(available_since)
        delete = policy.should_delete(available_since)
        days_left = policy.days_remaining(available_since)

        return RetentionResult(remind=remind, delete=delete, days_left=days_left)

    @property
    def policy(self) -> RetentionPolicy:
        """Get current policy (for backward compatibility)."""
        return self._get_policy()
