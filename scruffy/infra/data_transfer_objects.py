from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Union

from .constants import MediaStatus, RequestStatus


@dataclass(frozen=True)
class RequestDTO:
    user_id: int
    user_email: str
    type: Literal["movie", "tv"]
    request_id: int
    request_status: RequestStatus
    updated_at: datetime
    media_id: int
    media_status: MediaStatus
    external_service_id: int
    seasons: list[int]

    # TODO: Move to factory class, DTO should not be responsible for parsing responses
    @classmethod
    def from_overseer_response(cls, response: dict) -> "RequestDTO":
        media: dict = response.get("media", {})
        return cls(
            user_id=response.get("requestedBy", {}).get("id"),
            user_email=response.get("requestedBy", {}).get("email"),
            type=response["type"],
            request_id=response["id"],
            updated_at=datetime.fromisoformat(media["updatedAt"]),
            request_status=RequestStatus(response["status"]),
            media_id=media.get("id"),
            media_status=MediaStatus(media.get("status")),
            external_service_id=media.get("externalServiceId"),
            seasons=[season["seasonNumber"] for season in response.get("seasons", [])],
        )


@dataclass(frozen=True)
class MediaInfoDTO:
    """
    Returned Media information from Sonarr or Radarr API.
    This dataclass is used to check the age and size of the media on disk
    to determine if it should be removed or if the user should be reminded.

    We also store Title and image url information to be used in notifications.
    """

    available_since: Union[None, datetime]
    available: bool
    id: int
    poster: str
    seasons: list[int]
    size_on_disk: int
    title: str
