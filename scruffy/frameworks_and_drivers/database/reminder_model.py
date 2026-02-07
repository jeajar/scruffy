from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class ReminderModel(SQLModel, table=True):
    """
    SQLModel table definition for reminders.
    Takes the Request ID and store the reminder status
    whether it was sent to the user or not.
    """

    request_id: int = Field(primary_key=True)
    user_id: int
    date_sent: datetime = Field(default_factory=lambda: datetime.now(UTC))
