"""Background scheduler for scheduled check/process jobs."""

import asyncio
import logging
from typing import TYPE_CHECKING

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlmodel import Session, select

from scruffy.frameworks_and_drivers.database.database import get_engine
from scruffy.frameworks_and_drivers.database.job_run_store import record_job_run_sync
from scruffy.frameworks_and_drivers.database.schedule_model import ScheduleJobModel

if TYPE_CHECKING:
    from fastapi import FastAPI

logger = logging.getLogger(__name__)


def _make_job_runner(app: "FastAPI", job_type: str):
    """Return an async callable that runs the given job type using app.state.container."""

    async def _run() -> None:
        container = app.state.container
        success = False
        error_message: str | None = None
        try:
            if job_type == "check":
                await container.check_media_requests_use_case.execute_with_retention(
                    container.retention_calculator
                )
                logger.info("Scheduled check job completed")
            elif job_type == "process":
                await container.process_media_use_case.execute()
                logger.info("Scheduled process job completed")
            else:
                logger.warning("Unknown job_type in schedule: %s", job_type)
            success = True
        except Exception as e:
            error_message = str(e)
            logger.exception("Scheduled job %s failed: %s", job_type, e)
        finally:
            if job_type in ("check", "process"):
                await asyncio.to_thread(
                    record_job_run_sync, job_type, success, error_message
                )

    return _run


def start_scheduler(app: "FastAPI") -> None:
    """Create scheduler, load jobs from DB, start. Store scheduler on app.state.scheduler."""
    scheduler = AsyncIOScheduler()
    engine = get_engine()

    with Session(engine) as session:
        for row in session.exec(
            select(ScheduleJobModel).where(ScheduleJobModel.enabled)
        ).all():
            try:
                trigger = CronTrigger.from_crontab(row.cron_expression)
                runner = _make_job_runner(app, row.job_type)
                scheduler.add_job(
                    runner,
                    trigger,
                    id=f"schedule-{row.id}",
                    replace_existing=True,
                )
                logger.info(
                    "Scheduled job loaded",
                    extra={
                        "job_id": row.id,
                        "job_type": row.job_type,
                        "cron": row.cron_expression,
                    },
                )
            except Exception as e:
                logger.warning(
                    "Failed to load schedule job %s: %s",
                    row.id,
                    e,
                    extra={"job_type": row.job_type, "cron": row.cron_expression},
                )

    scheduler.start()
    app.state.scheduler = scheduler
    logger.info("Background scheduler started")


def shutdown_scheduler(app: "FastAPI") -> None:
    """Shut down the scheduler if present."""
    scheduler = getattr(app.state, "scheduler", None)
    if scheduler is not None:
        scheduler.shutdown(wait=False)
        logger.info("Background scheduler shut down")


def add_job_to_scheduler(app: "FastAPI", model: ScheduleJobModel) -> None:
    """Add or replace a single job. Call after inserting/updating model in DB."""
    if not model.enabled or model.id is None:
        return
    scheduler: AsyncIOScheduler | None = getattr(app.state, "scheduler", None)
    if scheduler is None:
        return
    job_id = f"schedule-{model.id}"
    try:
        trigger = CronTrigger.from_crontab(model.cron_expression)
        runner = _make_job_runner(app, model.job_type)
        scheduler.add_job(runner, trigger, id=job_id, replace_existing=True)
        logger.info(
            "Schedule job added",
            extra={
                "job_id": model.id,
                "job_type": model.job_type,
                "cron": model.cron_expression,
            },
        )
    except Exception as e:
        logger.warning("Failed to add schedule job %s: %s", model.id, e)


def remove_job_from_scheduler(app: "FastAPI", job_id: int) -> None:
    """Remove a job by schedule row id."""
    scheduler: AsyncIOScheduler | None = getattr(app.state, "scheduler", None)
    if scheduler is None:
        return
    sid = f"schedule-{job_id}"
    try:
        scheduler.remove_job(sid)
        logger.info("Schedule job removed", extra={"job_id": job_id})
    except Exception as e:
        logger.debug("Remove schedule job %s: %s", job_id, e)


def update_job_in_scheduler(app: "FastAPI", model: ScheduleJobModel) -> None:
    """Update a job (remove then add if enabled)."""
    if model.id is not None:
        remove_job_from_scheduler(app, model.id)
    if model.enabled:
        add_job_to_scheduler(app, model)
