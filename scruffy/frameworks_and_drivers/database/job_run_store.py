"""Store for recording job run history."""

import json
from typing import Any

from sqlmodel import Session

from scruffy.frameworks_and_drivers.database.database import get_engine
from scruffy.frameworks_and_drivers.database.job_run_model import JobRunModel


def record_job_run_sync(
    job_type: str,
    success: bool,
    error_message: str | None = None,
    summary: dict[str, Any] | None = None,
) -> None:
    """Insert a job run record into the database."""
    summary_json = json.dumps(summary) if summary is not None else None
    model = JobRunModel(
        job_type=job_type,
        success=success,
        error_message=error_message,
        summary=summary_json,
    )
    with Session(get_engine()) as session:
        session.add(model)
        session.commit()
