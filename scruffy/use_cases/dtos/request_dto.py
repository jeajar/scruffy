from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from scruffy.domain.value_objects.media_status import MediaStatus
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
        
        # Handle request status - Overseerr can return either integer or string
        raw_status = response.get("status")
        if raw_status is None:
            request_status = RequestStatus.PENDING_APPROVAL
        elif isinstance(raw_status, int):
            # Direct integer mapping to enum values
            try:
                request_status = RequestStatus(raw_status)
            except (ValueError, TypeError):
                request_status = RequestStatus.PENDING_APPROVAL
        else:
            # Map Overseerr status strings to RequestStatus enum
            status_map = {
                "pendingApproval": RequestStatus.PENDING_APPROVAL,
                "pendingapproval": RequestStatus.PENDING_APPROVAL,
                "approved": RequestStatus.APPROVED,
                "declined": RequestStatus.DECLINED,
            }
            request_status = status_map.get(str(raw_status).lower(), RequestStatus.PENDING_APPROVAL)
        
        # Handle media status - Overseerr can return either integer or string
        raw_media_status = media.get("status")
        if raw_media_status is None:
            media_status = MediaStatus.UNKNOWN
        elif isinstance(raw_media_status, int):
            # Direct integer mapping to enum values
            try:
                media_status = MediaStatus(raw_media_status)
            except (ValueError, TypeError):
                media_status = MediaStatus.UNKNOWN
        else:
            # Map Overseerr media status strings to MediaStatus enum
            media_status_map = {
                "unknown": MediaStatus.UNKNOWN,
                "pending": MediaStatus.PENDING,
                "processing": MediaStatus.PROCESSING,
                "partiallyAvailable": MediaStatus.PARTIALLY_AVAILABLE,
                "partiallyavailable": MediaStatus.PARTIALLY_AVAILABLE,
                "available": MediaStatus.AVAILABLE,
            }
            media_status_str = str(raw_media_status).lower()
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
