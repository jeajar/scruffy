"""Helpers for reading/writing admin settings from database."""

import logging

from sqlmodel import Session, select

from scruffy.frameworks_and_drivers.config.settings import settings
from scruffy.frameworks_and_drivers.database.database import get_engine
from scruffy.frameworks_and_drivers.database.settings_model import SettingsModel

logger = logging.getLogger(__name__)

EXTENSION_DAYS_KEY = "extension_days"


def get_extension_days() -> int:
    """
    Get extension_days setting.

    Resolution order: DB value if set, else env (settings.extension_days), else default 7.
    """
    engine = get_engine()
    with Session(engine) as session:
        model = session.get(SettingsModel, EXTENSION_DAYS_KEY)
        if model is not None:
            try:
                return int(model.value)
            except (ValueError, TypeError):
                logger.warning(
                    "Invalid extension_days in DB, using env default",
                    extra={"value": model.value},
                )
    return settings.extension_days


def set_extension_days(value: int) -> None:
    """Set extension_days in database."""
    engine = get_engine()
    with Session(engine) as session:
        model = session.get(SettingsModel, EXTENSION_DAYS_KEY)
        if model is None:
            model = SettingsModel(key=EXTENSION_DAYS_KEY, value=str(value))
            session.add(model)
        else:
            model.value = str(value)
        session.commit()
    logger.info("Updated extension_days setting", extra={"value": value})
