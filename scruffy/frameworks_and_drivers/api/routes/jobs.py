"""Admin routes for job run history."""

import asyncio
import json
import logging
from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import desc
from sqlmodel import Session, select

from scruffy.frameworks_and_drivers.api.auth import AdminUser
from scruffy.frameworks_and_drivers.database.database import get_engine
from scruffy.frameworks_and_drivers.database.job_run_model import JobRunModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/jobs", tags=["admin", "jobs"])

LIMIT = 100


class JobRunResponse(BaseModel):
    """Job run as returned by API."""

    id: int
    job_type: str
    finished_at: datetime
    success: bool
    error_message: str | None
    summary: dict | None = None


def _list_job_runs_sync(limit: int = LIMIT) -> list[JobRunModel]:
    engine = get_engine()
    with Session(engine) as session:
        return list(
            session.exec(
                select(JobRunModel)
                .order_by(desc(JobRunModel.finished_at))  # type: ignore[invalid-argument-type]
                .limit(limit)
            )
        )


def _parse_summary(summary_json: str | None) -> dict | None:
    """Parse summary JSON string to dict, or return None."""
    if summary_json is None:
        return None
    try:
        return json.loads(summary_json)
    except (json.JSONDecodeError, TypeError):
        return None


@router.get("", response_model=list[JobRunResponse])
async def list_job_runs(_user: AdminUser) -> list[JobRunResponse]:
    """List job runs, newest first. Admin only."""
    rows = await asyncio.to_thread(_list_job_runs_sync)
    return [
        JobRunResponse(
            id=r.id,
            job_type=r.job_type,
            finished_at=r.finished_at,
            success=r.success,
            error_message=r.error_message,
            summary=_parse_summary(r.summary),
        )
        for r in rows
        if r.id is not None
    ]
