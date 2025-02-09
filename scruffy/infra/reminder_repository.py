from sqlalchemy import Engine
from sqlmodel import Session, create_engine, select

from scruffy.models.reminder_model import Reminder


class ReminderRepository:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine or create_engine("sqlite:///scruffy.db")

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
