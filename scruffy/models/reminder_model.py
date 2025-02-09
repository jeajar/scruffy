from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class Reminder(SQLModel, table=True):
    """
    Takes the Request ID and store the reminder status
    wether it was sent to the user or not.
    """

    request_id: int = Field(primary_key=True)
    user_id: int
    date_sent: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
