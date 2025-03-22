from enum import Enum


class MediaStatus(Enum):
    UNKNOWN = 0
    PENDING = 1
    PROCESSING = 2
    AVAILABLE = 3
    UNAVAILABLE = 4
    # Add other statuses as needed

    @classmethod
    def from_value(cls, value: int) -> "MediaStatus":
        """Create MediaStatus from integer value."""
        try:
            return next(status for status in cls if status.value == value)
        except StopIteration:
            return cls.UNKNOWN


class RequestStatus(Enum):
    UNKNOWN = 0
    PENDING = 1
    APPROVED = 2
    DECLINED = 3
    # Add other statuses as needed

    @classmethod
    def from_value(cls, value: int) -> "RequestStatus":
        """Create RequestStatus from integer value."""
        try:
            return next(status for status in cls if status.value == value)
        except StopIteration:
            return cls.UNKNOWN
