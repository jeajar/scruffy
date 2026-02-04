from pathlib import Path

from sqlalchemy import Engine
from sqlmodel import SQLModel, create_engine

from scruffy.frameworks_and_drivers.config.settings import settings
from scruffy.frameworks_and_drivers.database.extension_model import (
    RequestExtensionModel,
)
from scruffy.frameworks_and_drivers.database.settings_model import SettingsModel


def get_engine() -> Engine:
    """Get or create database engine."""
    db_path = Path("scruffy.db")
    if settings.data_dir:
        db_path = Path(settings.data_dir) / "scruffy.db"
    engine = create_engine(f"sqlite:///{db_path}")
    SQLModel.metadata.create_all(engine)
    return engine
