"""Admin routes for job run history."""

import asyncio
import json
import logging
from datetime import datetime

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import desc, func
from sqlmodel import Session, select

from scruffy.frameworks_and_drivers.api.auth import AdminUser
from scruffy.frameworks_and_drivers.database.database import get_engine
from scruffy.frameworks_and_drivers.database.job_run_model import JobRunModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/jobs", tags=["admin", "jobs"])


class JobRunResponse(BaseModel):
    """Job run as returned by API."""

    id: int
    job_type: str
    finished_at: datetime
    success: bool
    error_message: str | None
    summary: dict | None = None


class PaginatedJobRunResponse(BaseModel):
    """Paginated list of job runs."""

    items: list[JobRunResponse]
    total: int
    page: int
    page_size: int | None


def _list_job_runs_sync(
    offset: int = 0,
    limit: int | None = 25,
) -> tuple[list[JobRunModel], int]:
    engine = get_engine()
    with Session(engine) as session:
        count_query = select(func.count()).select_from(JobRunModel)
        total = session.exec(count_query).one()

        query = (
            select(JobRunModel)
            .order_by(desc(JobRunModel.finished_at))  # type: ignore[invalid-argument-type]
            .offset(offset)
        )
        if limit is not None:
            query = query.limit(limit)

        rows = list(session.exec(query))
        return rows, int(total)


def _parse_summary(summary_json: str | None) -> dict | None:
    """Parse summary JSON string to dict, or return None."""
    if summary_json is None:
        return None
    try:
        return json.loads(summary_json)
    except (json.JSONDecodeError, TypeError):
        return None


@router.get("", response_model=PaginatedJobRunResponse)
async def list_job_runs(
    _user: AdminUser,
    page: int = Query(default=1, ge=1),
    page_size: int | None = Query(default=25, ge=0),
) -> PaginatedJobRunResponse:
    """List job runs, newest first. Admin only."""
    normalized_page_size: int | None = None if page_size == 0 else page_size
    offset = 0 if normalized_page_size is None else (page - 1) * normalized_page_size

    rows, total = await asyncio.to_thread(
        _list_job_runs_sync,
        offset,
        normalized_page_size,
    )
    items = [
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
    return PaginatedJobRunResponse(
        items=items,
        total=total,
        page=page,
        page_size=normalized_page_size,
    )
