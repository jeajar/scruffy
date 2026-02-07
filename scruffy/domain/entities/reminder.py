from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Reminder:
    """Core business entity for reminders."""

    request_id: int
    user_id: int
    date_sent: datetime
