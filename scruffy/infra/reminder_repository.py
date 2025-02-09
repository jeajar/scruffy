from pathlib import Path

from sqlalchemy import Engine
from sqlmodel import Session, SQLModel, create_engine, select

from scruffy.infra import settings
from scruffy.models.reminder_model import Reminder


class ReminderRepository:
    def __init__(self, engine: Engine = None) -> None:
        db_path = Path("scruffy.db")
        if settings.data_dir:
            db_path = Path(settings.data_dir) / "scruffy.db"
        self.engine = engine or create_engine(f"sqlite:///{db_path}")
        SQLModel.metadata.create_all(self.engine)

    def has_reminder(self, request_id: int) -> bool:
        with Session(self.engine) as session:
            statement = select(Reminder).where(Reminder.request_id == request_id)
            result = session.exec(statement).first()
            return result is not None

    def add_reminder(self, request_id: int, user_id: int) -> None:
        with Session(self.engine) as session:
            reminder = Reminder(request_id=request_id, user_id=user_id)
            session.add(reminder)
            session.commit()
