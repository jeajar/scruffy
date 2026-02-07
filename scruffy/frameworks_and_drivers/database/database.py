from pathlib import Path

from sqlalchemy import Engine, text
from sqlalchemy.exc import OperationalError
from sqlmodel import SQLModel, create_engine

from scruffy.frameworks_and_drivers.config.settings import settings


def _migrate_job_run_summary(engine: Engine) -> None:
    """Add summary column to jobrunmodel if missing (one-off migration for existing DBs)."""
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE jobrunmodel ADD COLUMN summary TEXT"))
        conn.commit()


def _migrate_schedule_job_type_unique(engine: Engine) -> None:
    """Add unique constraint on schedulejobmodel.job_type (one-off migration for existing DBs)."""
    with engine.connect() as conn:
        try:
            conn.execute(text("DROP INDEX IF EXISTS ix_schedulejobmodel_job_type"))
            conn.commit()
        except OperationalError:
            conn.rollback()
        try:
            conn.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS ix_schedulejobmodel_job_type "
                    "ON schedulejobmodel (job_type)"
                )
            )
            conn.commit()
        except OperationalError as e:
            conn.rollback()
            if (
                "already exists" not in str(e).lower()
                and "duplicate" not in str(e).lower()
            ):
                raise


def get_engine() -> Engine:
    """Get or create database engine."""
    db_path = Path("scruffy.db")
    if settings.data_dir:
        db_path = Path(settings.data_dir) / "scruffy.db"
    engine = create_engine(f"sqlite:///{db_path}")
    SQLModel.metadata.create_all(engine)
    try:
        _migrate_job_run_summary(engine)
    except OperationalError as e:
        if "duplicate column name" not in str(e).lower():
            raise
    try:
        _migrate_schedule_job_type_unique(engine)
    except OperationalError:
        pass  # Fresh installs: create_all already created unique index
    return engine


def reset_engine_for_testing() -> None:
    """Clear any cached engine so tests get a fresh engine with patched settings.

    No-op when get_engine() does not cache (current implementation).
    Exists so tests can call it before patching settings.data_dir.
    """
