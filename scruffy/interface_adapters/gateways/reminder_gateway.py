"""Gateway adapter for reminder persistence."""

import logging
from typing import cast

from sqlalchemy import ColumnElement, Engine
from sqlmodel import Session, SQLModel, select

from scruffy.frameworks_and_drivers.database.database import get_engine
from scruffy.frameworks_and_drivers.database.reminder_model import ReminderModel
from scruffy.use_cases.interfaces.reminder_repository_interface import (
    ReminderRepositoryInterface,
)

logger = logging.getLogger(__name__)


class ReminderGateway(ReminderRepositoryInterface):
    """Adapter for reminder persistence using SQLModel."""

    def __init__(self, engine: Engine | None = None):
        """Initialize reminder gateway with database engine."""
        self.engine = engine or get_engine()
        SQLModel.metadata.create_all(self.engine)
        logger.debug("Initialized ReminderGateway")

    def has_reminder(self, request_id: int) -> bool:
        """Check if a reminder has been sent for a request."""
        with Session(self.engine) as session:
            statement = select(ReminderModel).where(
                ReminderModel.request_id == request_id
            )
            result = session.exec(statement).first()
            has_reminder = result is not None
            logger.debug(
                "Checked reminder status",
                extra={"request_id": request_id, "has_reminder": has_reminder},
            )
            return has_reminder

    def add_reminder(self, request_id: int, user_id: int) -> None:
        """Add a reminder record."""
        logger.info(
            "Adding reminder record",
            extra={"request_id": request_id, "user_id": user_id},
        )
        with Session(self.engine) as session:
            reminder = ReminderModel(request_id=request_id, user_id=user_id)
            session.add(reminder)
            session.commit()
        logger.debug(
            "Reminder record added successfully",
            extra={"request_id": request_id, "user_id": user_id},
        )

    def get_request_ids_with_reminders(self, request_ids: list[int]) -> set[int]:
        """Return set of request_ids that have reminder records."""
        if not request_ids:
            return set()
        with Session(self.engine) as session:
            # SQLModel types request_id as int; at runtime it's a column with .in_()
            request_id_col = cast(ColumnElement[int], ReminderModel.request_id)
            statement = select(ReminderModel.request_id).where(
                request_id_col.in_(request_ids)
            )
            rows = session.exec(statement).all()
            result = set(rows)
            logger.debug(
                "Batch checked reminder status",
                extra={
                    "requested_count": len(request_ids),
                    "with_reminders_count": len(result),
                },
            )
            return result
