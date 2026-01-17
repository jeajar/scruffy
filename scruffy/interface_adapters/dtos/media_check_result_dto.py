"""DTOs for media check results."""

from dataclasses import dataclass

from scruffy.interface_adapters.dtos.media_info_dto import MediaInfoDTO
from scruffy.interface_adapters.dtos.request_dto import RequestDTO


@dataclass(frozen=True)
class RetentionResultDTO:
    """DTO for retention calculation results."""

    remind: bool
    delete: bool
    days_left: int = 0


@dataclass(frozen=True)
class MediaCheckResultDTO:
    """DTO for media check results including retention information."""

    request: RequestDTO
    media: MediaInfoDTO
    retention: RetentionResultDTO
