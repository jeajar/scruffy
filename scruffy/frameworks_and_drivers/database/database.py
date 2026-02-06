from pathlib import Path

from sqlalchemy import Engine
from sqlmodel import SQLModel, create_engine

from scruffy.frameworks_and_drivers.config.settings import settings


def get_engine() -> Engine:
    """Get or create database engine."""
    db_path = Path("scruffy.db")
    if settings.data_dir:
        db_path = Path(settings.data_dir) / "scruffy.db"
    engine = create_engine(f"sqlite:///{db_path}")
    SQLModel.metadata.create_all(engine)
    return engine


def reset_engine_for_testing() -> None:
    """Clear any cached engine so tests get a fresh engine with patched settings.

    No-op when get_engine() does not cache (current implementation).
    Exists so tests can call it before patching settings.data_dir.
    """
