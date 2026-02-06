"""Store for recording job run history."""

from sqlmodel import Session

from scruffy.frameworks_and_drivers.database.database import get_engine
from scruffy.frameworks_and_drivers.database.job_run_model import JobRunModel


def record_job_run_sync(
    job_type: str, success: bool, error_message: str | None = None
) -> None:
    """Insert a job run record into the database."""
    model = JobRunModel(
        job_type=job_type,
        success=success,
        error_message=error_message,
    )
    with Session(get_engine()) as session:
        session.add(model)
        session.commit()
