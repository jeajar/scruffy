from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from scruffy.domain.entities.media_request import MediaRequest
from scruffy.domain.value_objects.media_status import MediaStatus
from scruffy.domain.value_objects.media_type import MediaType
from scruffy.domain.value_objects.request_status import RequestStatus


@dataclass(frozen=True)
class RequestDTO:
    """Data Transfer Object for media requests."""

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

    @classmethod
    def from_overseer_response(cls, response: dict) -> "RequestDTO":
        """Create DTO from Overseerr API response."""
        media: dict = response.get("media", {})
        
        # Map Overseerr status strings to RequestStatus enum
        status_map = {
            "pendingApproval": RequestStatus.PENDING_APPROVAL,
            "approved": RequestStatus.APPROVED,
            "declined": RequestStatus.DECLINED,
        }
        request_status = status_map.get(response.get("status", "").lower(), RequestStatus.PENDING_APPROVAL)
        
        # Map Overseerr media status strings to MediaStatus enum
        media_status_map = {
            "unknown": MediaStatus.UNKNOWN,
            "pending": MediaStatus.PENDING,
            "processing": MediaStatus.PROCESSING,
            "partiallyAvailable": MediaStatus.PARTIALLY_AVAILABLE,
            "available": MediaStatus.AVAILABLE,
        }
        media_status_str = str(media.get("status", "")).lower()
        media_status = media_status_map.get(media_status_str, MediaStatus.UNKNOWN)
        
        return cls(
            user_id=response.get("requestedBy", {}).get("id"),
            user_email=response.get("requestedBy", {}).get("email"),
            type=response["type"],
            request_id=response["id"],
            updated_at=datetime.fromisoformat(media["updatedAt"]),
            request_status=request_status,
            media_id=media.get("id"),
            media_status=media_status,
            external_service_id=media.get("externalServiceId"),
            seasons=[season["seasonNumber"] for season in response.get("seasons", [])],
        )

    def to_domain_entity(self) -> MediaRequest:
        """Convert DTO to domain entity."""
        media_type = MediaType.MOVIE if self.type == "movie" else MediaType.TV
        return MediaRequest(
            user_id=self.user_id,
            user_email=self.user_email,
            media_type=media_type,
            request_id=self.request_id,
            request_status=self.request_status,
            updated_at=self.updated_at,
            media_id=self.media_id,
            media_status=self.media_status,
            external_service_id=self.external_service_id,
            seasons=self.seasons,
        )

    def json(self):
        """Convert to JSON-serializable dict."""
        return {
            "user_id": int(self.user_id),
            "user_email": str(self.user_email),
            "type": str(self.type),
            "request_id": int(self.request_id),
            "request_status": self.request_status.name,
            "updated_at": self.updated_at.isoformat(),
            "media_id": int(self.media_id),
            "media_status": self.media_status.name,
            "external_service_id": int(self.external_service_id),
            "seasons": list(self.seasons),
        }
