from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Union

from .constants import MediaStatus, RequestStatus


@dataclass(frozen=True)
class RequestDTO:
    user_id: int
    type: Literal["movie", "tv"]
    request_id: int
    request_status: RequestStatus
    updated_at: datetime
    media_status: MediaStatus
    external_service_id: int
    seasons: list[int]

    @classmethod
    def from_overseer_response(cls, response: dict) -> "RequestDTO":
        media: dict = response.get("media", {})
        return cls(
            user_id=response.get("requestedBy", {}).get("id"),
            type=response["type"],
            request_id=response["id"],
            updated_at=datetime.fromisoformat(media["updatedAt"]),
            request_status=RequestStatus(response["status"]),
            media_status=MediaStatus(media.get("status")),
            external_service_id=media.get("externalServiceId"),
            seasons=[season["seasonNumber"] for season in response.get("seasons", [])],
        )


@dataclass(frozen=True)
class MovieInfoDTO:
    """
    Returned information on Requested Movie from Radarr. This represents a request
    for a single movie. We check that the requested movie is available on disk
    """

    title: str
    available: bool
    available_since: Union[None, datetime]
    size_on_disk: int
    movie_id: int

    @classmethod
    def from_radarr_response(cls, response: dict) -> "MovieInfoDTO":
        added_at = response.get("movieFile", {}).get("dateAdded")
        return cls(
            title=response.get("title"),
            available=response.get("hasFile"),
            available_since=datetime.fromisoformat(added_at) if added_at else None,
            size_on_disk=response.get("sizeOnDisk"),
            movie_id=response.get("id"),
        )


# TODO: This and MovieInforDTO are very similar. Consider refactoring to a base class
@dataclass(frozen=True)
class TvInfoDTO:
    """
    Returned information on Requested Tv Show from Sonarr. This represents a request
    for a show with a any numbers of seasons. We check that all requested seasons'
    episodes are available on disk and return the latest added as a available_since
    timestamp.

    Attributes:
        title: The title of the TV show returned by Sonarr
        available: Whether all requested episodes are available
        available_since: The date the latest episode was added on disk
        size_on_disk: The total size of all requested episodes
        seasons: The season number of the requested episodes
        series_id: The Sonarr internal ID of the series
    """

    title: str
    available: bool
    available_since: Union[None, datetime]
    size_on_disk: int
    seasons: list[int]
    series_id: int
