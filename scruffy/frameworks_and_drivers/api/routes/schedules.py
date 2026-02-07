"""Admin routes for scheduled jobs (check/process)."""

import asyncio
import logging
from datetime import UTC, datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from scruffy.frameworks_and_drivers.api.auth import AdminUser
from scruffy.frameworks_and_drivers.api.dependencies import ContainerDep
from scruffy.frameworks_and_drivers.api.scheduler import (
    add_job_to_scheduler,
    remove_job_from_scheduler,
    update_job_in_scheduler,
)
from scruffy.frameworks_and_drivers.database.database import get_engine
from scruffy.frameworks_and_drivers.database.job_run_store import record_job_run_sync
from scruffy.frameworks_and_drivers.database.schedule_model import ScheduleJobModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/schedules", tags=["admin", "schedules"])


# --- Schemas ---


class ScheduleCreate(BaseModel):
    """Payload to create a schedule."""

    job_type: str = Field(..., pattern="^(check|process)$")
    cron_expression: str = Field(
        ..., min_length=9, description="5-field cron: minute hour day month dow"
    )
    enabled: bool = True


class ScheduleUpdate(BaseModel):
    """Payload to update a schedule."""

    job_type: str | None = Field(None, pattern="^(check|process)$")
    cron_expression: str | None = Field(None, min_length=9)
    enabled: bool | None = None


class ScheduleResponse(BaseModel):
    """Schedule as returned by API."""

    id: int
    job_type: str
    cron_expression: str
    enabled: bool
    created_at: datetime
    updated_at: datetime


def _to_response(model: ScheduleJobModel) -> ScheduleResponse:
    if model.id is None:
        raise ValueError("ScheduleJobModel must have id for response")
    return ScheduleResponse(
        id=model.id,
        job_type=model.job_type,
        cron_expression=model.cron_expression,
        enabled=model.enabled,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


# --- Sync DB helpers (run in thread pool to avoid blocking event loop) ---


def _list_schedules_sync() -> list[ScheduleJobModel]:
    engine = get_engine()
    with Session(engine) as session:
        return list(session.exec(select(ScheduleJobModel).order_by("id")))


def _create_schedule_sync(body: ScheduleCreate) -> ScheduleJobModel:
    engine = get_engine()
    model = ScheduleJobModel(
        job_type=body.job_type,
        cron_expression=body.cron_expression.strip(),
        enabled=body.enabled,
    )
    with Session(engine) as session:
        session.add(model)
        session.commit()
        session.refresh(model)
    if model.id is None:
        raise HTTPException(status_code=500, detail="Failed to create schedule")
    return model


def _get_schedule_sync(schedule_id: int) -> ScheduleJobModel | None:
    engine = get_engine()
    with Session(engine) as session:
        return session.get(ScheduleJobModel, schedule_id)


def _update_schedule_sync(schedule_id: int, body: ScheduleUpdate) -> ScheduleJobModel:
    engine = get_engine()
    with Session(engine) as session:
        model = session.get(ScheduleJobModel, schedule_id)
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schedule not found",
            )
        if body.job_type is not None:
            model.job_type = body.job_type
        if body.cron_expression is not None:
            model.cron_expression = body.cron_expression.strip()
        if body.enabled is not None:
            model.enabled = body.enabled
        model.updated_at = datetime.now(UTC)
        session.add(model)
        session.commit()
        session.refresh(model)
    return model


def _delete_schedule_sync(schedule_id: int) -> None:
    engine = get_engine()
    with Session(engine) as session:
        model = session.get(ScheduleJobModel, schedule_id)
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schedule not found",
            )
        session.delete(model)
        session.commit()


def _get_schedule_job_type_sync(schedule_id: int) -> str | None:
    engine = get_engine()
    with Session(engine) as session:
        model = session.get(ScheduleJobModel, schedule_id)
        return model.job_type if model else None


# --- Routes ---


@router.get("", response_model=list[ScheduleResponse])
async def list_schedules(_user: AdminUser) -> list[ScheduleResponse]:
    """List all scheduled jobs. Admin only."""
    rows = await asyncio.to_thread(_list_schedules_sync)
    return [_to_response(r) for r in rows]


@router.post("", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    body: ScheduleCreate,
    request: Request,
    _user: AdminUser,
) -> ScheduleResponse:
    """Create a new schedule. Admin only."""
    model = await asyncio.to_thread(_create_schedule_sync, body)
    add_job_to_scheduler(request.app, model)
    logger.info(
        "Schedule created",
        extra={"job_id": model.id, "job_type": model.job_type},
    )
    return _to_response(model)


@router.get("/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(schedule_id: int, _user: AdminUser) -> ScheduleResponse:
    """Get a single schedule by id. Admin only."""
    model = await asyncio.to_thread(_get_schedule_sync, schedule_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found"
        )
    return _to_response(model)


@router.patch("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: int,
    body: ScheduleUpdate,
    request: Request,
    _user: AdminUser,
) -> ScheduleResponse:
    """Update a schedule. Admin only."""
    model = await asyncio.to_thread(_update_schedule_sync, schedule_id, body)
    update_job_in_scheduler(request.app, model)
    logger.info("Schedule updated", extra={"job_id": schedule_id})
    return _to_response(model)


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: int,
    request: Request,
    _user: AdminUser,
) -> None:
    """Delete a schedule. Admin only."""
    await asyncio.to_thread(_delete_schedule_sync, schedule_id)
    remove_job_from_scheduler(request.app, schedule_id)
    logger.info("Schedule deleted", extra={"job_id": schedule_id})


async def _run_job_now(container: ContainerDep, job_type: str) -> None:
    """Background helper to run check or process once."""
    success = False
    error_message: str | None = None
    summary = None
    try:
        if job_type == "check":
            results = (
                await container.check_media_requests_use_case.execute_with_retention(
                    container.retention_calculator
                )
            )
            summary = {
                "items_checked": len(results),
                "needing_attention": sum(
                    1 for r in results if r.retention.remind or r.retention.delete
                ),
            }
        elif job_type == "process":
            summary = await container.process_media_use_case.execute()
        logger.info("Run-now job completed", extra={"job_type": job_type})
        success = True
    except Exception as e:
        error_message = str(e)
        logger.exception("Run-now job %s failed: %s", job_type, e)
    finally:
        await asyncio.to_thread(
            record_job_run_sync, job_type, success, error_message, summary
        )


@router.post("/{schedule_id}/run")
async def run_schedule_now(
    schedule_id: int,
    background_tasks: BackgroundTasks,
    container: ContainerDep,
    _user: AdminUser,
) -> dict:
    """Run this schedule's job once now (in background). Admin only."""
    job_type = await asyncio.to_thread(_get_schedule_job_type_sync, schedule_id)
    if not job_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found"
        )
    background_tasks.add_task(_run_job_now, container, job_type)
    return {
        "status": "started",
        "job_type": job_type,
        "message": "Job started in background",
    }
