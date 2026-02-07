from dataclasses import dataclass
from datetime import datetime

from scruffy.domain.value_objects.media_status import MediaStatus
from scruffy.domain.value_objects.media_type import MediaType
from scruffy.domain.value_objects.request_status import RequestStatus


@dataclass(frozen=True)
class MediaRequest:
    """Core business entity representing a media request."""

    user_id: int
    user_email: str
    media_type: MediaType
    request_id: int
    request_status: RequestStatus
    updated_at: datetime
    media_id: int
    media_status: MediaStatus
    external_service_id: int
    seasons: list[int]
