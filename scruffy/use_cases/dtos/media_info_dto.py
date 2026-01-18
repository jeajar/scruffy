from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class MediaInfoDTO:
    """
    Data Transfer Object for media information from Sonarr or Radarr API.
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
