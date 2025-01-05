from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from .constants import MediaStatus, RequestStatus


@dataclass(frozen=True)
class Request:
    user_id: int
    type: Literal["movie", "tv"]
    request_id: int
    request_status: RequestStatus
    updated_at: datetime
    MediaStatus: MediaStatus
    sonarr_id: int
    seasons: list[int]

    @classmethod
    def from_overseer_response(cls, response: dict) -> "Request":
        media: dict = response.get("media", {})
        return cls(
            user_id=response.get("requestedBy", {}).get("id"),
            type=response["type"],
            request_id=response["id"],
            updated_at=datetime.fromisoformat(media["updatedAt"]),
            request_status=RequestStatus(response["status"]),
            MediaStatus=MediaStatus(media.get("status")),
            sonarr_id=media.get("externalServiceId"),
            seasons=[season["seasonNumber"] for season in response.get("seasons", [])],
        )
