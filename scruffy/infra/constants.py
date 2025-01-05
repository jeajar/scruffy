from enum import Enum


class MediaStatus(Enum):
    UNKNOWN = 1
    PENDING = 2
    PROCESSING = 3
    PARTIALLY_AVAILABLE = 4
    AVAILABLE = 5


class RequestStatus(Enum):
    PENDING_APPROVAL = 1
    APPROVED = 2
    DECLINED = 3
