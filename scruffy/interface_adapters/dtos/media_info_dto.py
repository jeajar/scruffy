from dataclasses import dataclass
from datetime import datetime

from scruffy.domain.entities.media import Media


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

    def to_domain_entity(self) -> Media:
        """Convert DTO to domain entity."""
        return Media(
            id=self.id,
            title=self.title,
            available=self.available,
            available_since=self.available_since,
            size_on_disk=self.size_on_disk,
            poster=self.poster,
            seasons=self.seasons,
        )
