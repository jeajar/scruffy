"""Gateway adapter for request extension persistence."""

import logging

from sqlalchemy import Engine
from sqlmodel import Session, SQLModel, select

from scruffy.frameworks_and_drivers.database.database import get_engine
from scruffy.frameworks_and_drivers.database.extension_model import RequestExtensionModel
from scruffy.use_cases.interfaces.extension_repository_interface import (
    ExtensionRepositoryInterface,
)

logger = logging.getLogger(__name__)


class ExtensionGateway(ExtensionRepositoryInterface):
    """Adapter for request extension persistence using SQLModel."""

    def __init__(self, engine: Engine | None = None):
        """Initialize extension gateway with database engine."""
        self.engine = engine or get_engine()
        SQLModel.metadata.create_all(self.engine)
        logger.debug("Initialized ExtensionGateway")

    def is_extended(self, request_id: int) -> bool:
        """Check if a request has been extended."""
        with Session(self.engine) as session:
            statement = select(RequestExtensionModel).where(
                RequestExtensionModel.request_id == request_id
            )
            result = session.exec(statement).first()
            has_extension = result is not None
            logger.debug(
                "Checked extension status",
                extra={"request_id": request_id, "is_extended": has_extension},
            )
            return has_extension

    def extend_request(self, request_id: int, plex_user_id: int) -> bool:
        """
        Record an extension for a request.

        Returns True if extended, False if already extended.
        """
        if self.is_extended(request_id):
            logger.debug(
                "Request already extended, skipping",
                extra={"request_id": request_id},
            )
            return False

        logger.info(
            "Recording request extension",
            extra={"request_id": request_id, "plex_user_id": plex_user_id},
        )
        with Session(self.engine) as session:
            extension = RequestExtensionModel(
                request_id=request_id,
                extended_by_plex_id=plex_user_id,
            )
            session.add(extension)
            session.commit()
        logger.debug(
            "Request extension recorded successfully",
            extra={"request_id": request_id},
        )
        return True

    def get_extended_request_ids(self) -> set[int]:
        """Get all request IDs that have been extended."""
        with Session(self.engine) as session:
            statement = select(RequestExtensionModel.request_id)
            results = session.exec(statement).all()
            ids = set(results)
            logger.debug(
                "Retrieved extended request IDs",
                extra={"count": len(ids)},
            )
            return ids
