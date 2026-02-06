from pathlib import Path

from sqlalchemy import Engine
from sqlmodel import SQLModel, create_engine

from scruffy.frameworks_and_drivers.config.settings import settings
from scruffy.frameworks_and_drivers.database.extension_model import (
    RequestExtensionModel,
)
from scruffy.frameworks_and_drivers.database.job_run_model import JobRunModel
from scruffy.frameworks_and_drivers.database.settings_model import SettingsModel

_engine: Engine | None = None


def reset_engine_for_testing() -> None:
    """Reset the engine singleton. For testing only; allows tests to get a fresh engine with updated settings."""
    global _engine
    _engine = None


def get_engine() -> Engine:
    """Get or create database engine (singleton)."""
    global _engine
    if _engine is None:
        db_path = Path("scruffy.db")
        if settings.data_dir:
            db_path = Path(settings.data_dir) / "scruffy.db"
        _engine = create_engine(f"sqlite:///{db_path}")
        SQLModel.metadata.create_all(_engine)
    return _engine
