from dataclasses import dataclass
from datetime import datetime
from typing import Literal


@dataclass(frozen=True)
class RequestDTO:
    user_id: int
    user_email: str
    type_: Literal["movie", "tv"]
    request_id: int
    request_status: int
    updated_at: datetime
    media_id: int
    media_status: int
    external_service_id: int
    seasons: list[int]


@dataclass(frozen=True)
class MediaInfoDTO:
    """
    Returned Media information from Sonarr or Radarr API.
    This dataclass is used to check the age and size of the media on disk
    to determine if it should be removed or if the user should be reminded.

    We also store Title and image url information to be used in notifications.
    """

    available_since: None | datetime
    available: bool
    id: int
    poster: str
    seasons: list[int]
    size_on_disk: int
    title: str
