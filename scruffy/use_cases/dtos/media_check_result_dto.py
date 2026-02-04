"""DTOs for media check results."""

from dataclasses import dataclass

from scruffy.use_cases.dtos.media_info_dto import MediaInfoDTO
from scruffy.use_cases.dtos.request_dto import RequestDTO


@dataclass(frozen=True)
class RetentionResultDTO:
    """DTO for retention calculation results."""

    remind: bool
    delete: bool
    days_left: int = 0
    extended: bool = False


@dataclass(frozen=True)
class MediaCheckResultDTO:
    """DTO for media check results including retention information."""

    request: RequestDTO
    media: MediaInfoDTO
    retention: RetentionResultDTO
