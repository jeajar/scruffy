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
class MediaInfoDTO:
    available_since: Union[None, datetime]
    available: bool
    id: int
    seasons: list[int]
    size_on_disk: int
    title: str

    @classmethod
    def from_radarr_response(cls, response: dict) -> "MediaInfoDTO":
        added_at = response.get("movieFile", {}).get("dateAdded")
        return cls(
            title=response.get("title"),
            available=response.get("hasFile"),
            available_since=datetime.fromisoformat(added_at) if added_at else None,
            size_on_disk=response.get("sizeOnDisk"),
            id=response.get("id"),
            seasons=[],
        )
