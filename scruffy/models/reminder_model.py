from sqlmodel import SQLModel


class Reminder(SQLModel, table=True):
    """
    Takes the Request ID and store the reminder status
    wether it was sent to the user or not.
    """

    id: int
    sent: bool
