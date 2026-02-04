"""Abstract interface for request extension persistence."""

from abc import ABC, abstractmethod


class ExtensionRepositoryInterface(ABC):
    """Abstract interface for request extension persistence."""

    @abstractmethod
    def is_extended(self, request_id: int) -> bool:
        """Check if a request has been extended."""
        pass

    @abstractmethod
    def extend_request(self, request_id: int, plex_user_id: int) -> bool:
        """
        Record an extension for a request.

        Returns True if extended, False if already extended.
        """
        pass

    @abstractmethod
    def get_extended_request_ids(self) -> set[int]:
        """Get all request IDs that have been extended."""
        pass
