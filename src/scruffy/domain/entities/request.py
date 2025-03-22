from dataclasses import dataclass
from datetime import datetime


@dataclass
class Request:
    """Domain entity representing a media request."""

    id: int
    media_id: int
    type: str  # 'movie' or 'tv'
    title: str
    status: str
    created_at: datetime
    updated_at: datetime
    requested_by: str
    user_email: str | None = None
