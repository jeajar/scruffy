from sqlmodel import Session, select

from scruffy.infra.data_transfer_objects import RequestDTO
from scruffy.models.reminder_model import Reminder


class ReminderRepository:
    def __init__(self, session: Session):
        self.session = session

    async def get_reminder_status(self, request: RequestDTO) -> bool:
        """
        Check if a reminder was sent for a specific request.

        Args:
            request: The request to check reminder status for

        Returns:
            bool: True if reminder was sent, False otherwise
        """
        statement = select(Reminder).where(Reminder.id == request.request_id)
        result = self.session.exec(statement).first()
        return result.sent if result else False

    async def set_reminder_sent(self, request: RequestDTO) -> None:
        """
        Mark a reminder as sent for a specific request.

        Args:
            request: The request to mark reminder as sent
        """
        reminder = Reminder(id=request.request_id, sent=True)
        self.session.merge(reminder)
        self.session.commit()
