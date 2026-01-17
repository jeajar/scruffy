from sqlalchemy import Engine
from sqlmodel import Session, SQLModel, select

from scruffy.frameworks_and_drivers.database.database import get_engine
from scruffy.frameworks_and_drivers.database.reminder_model import ReminderModel
from scruffy.use_cases.interfaces.reminder_repository_interface import (
    ReminderRepositoryInterface,
)


class ReminderGateway(ReminderRepositoryInterface):
    """Adapter for reminder persistence using SQLModel."""

    def __init__(self, engine: Engine | None = None):
        """Initialize reminder gateway with database engine."""
        self.engine = engine or get_engine()
        SQLModel.metadata.create_all(self.engine)

    def has_reminder(self, request_id: int) -> bool:
        """Check if a reminder has been sent for a request."""
        with Session(self.engine) as session:
            statement = select(ReminderModel).where(
                ReminderModel.request_id == request_id
            )
            result = session.exec(statement).first()
            return result is not None

    def add_reminder(self, request_id: int, user_id: int) -> None:
        """Add a reminder record."""
        with Session(self.engine) as session:
            reminder = ReminderModel(request_id=request_id, user_id=user_id)
            session.add(reminder)
            session.commit()
