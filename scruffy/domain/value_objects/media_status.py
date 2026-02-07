from enum import Enum


class MediaStatus(Enum):
    """Media availability status."""

    UNKNOWN = 1
    PENDING = 2
    PROCESSING = 3
    PARTIALLY_AVAILABLE = 4
    AVAILABLE = 5
