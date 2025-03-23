from dataclasses import dataclass
from datetime import datetime
from typing import Literal


@dataclass(frozen=True)
class RequestDTO:
    user_id: int
    user_email: str
    type_: Literal["movie", "tv"]
    request_id: int
    request_status: int
    updated_at: datetime
    media_id: int
    media_status: int
    external_service_id: int
    seasons: list[int]
