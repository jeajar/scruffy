from enum import Enum


class RequestStatus(Enum):
    """Request approval status."""

    PENDING_APPROVAL = 1
    APPROVED = 2
    DECLINED = 3
