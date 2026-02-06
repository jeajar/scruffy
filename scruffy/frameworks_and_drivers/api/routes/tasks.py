"""Background task routes for cron job replacement."""

import asyncio
import logging
from dataclasses import asdict

from fastapi import APIRouter, BackgroundTasks

from scruffy.frameworks_and_drivers.api.auth import ApiKeyAuth
from scruffy.frameworks_and_drivers.api.dependencies import ContainerDep
from scruffy.frameworks_and_drivers.database.job_run_store import record_job_run_sync

logger = logging.getLogger(__name__)

router = APIRouter(tags=["tasks"])


async def _run_check_task(container):
    """Background task to run check use case."""
    success = False
    error_message: str | None = None
    summary = None
    try:
        results = await container.check_media_requests_use_case.execute_with_retention(
            container.retention_calculator
        )
        summary = {
            "items_checked": len(results),
            "needing_attention": sum(
                1 for r in results if r.retention.remind or r.retention.delete
            ),
        }
        logger.info(
            "Check task completed",
            extra={"results_count": len(results)},
        )
        success = True
    except Exception as e:
        error_message = str(e)
        logger.error("Check task failed", extra={"error": str(e)})
    finally:
        await asyncio.to_thread(
            record_job_run_sync, "check", success, error_message, summary
        )


async def _run_process_task(container):
    """Background task to run process use case."""
    success = False
    error_message: str | None = None
    summary = None
    try:
        summary = await container.process_media_use_case.execute()
        logger.info("Process task completed")
        success = True
    except Exception as e:
        error_message = str(e)
        logger.error("Process task failed", extra={"error": str(e)})
    finally:
        await asyncio.to_thread(
            record_job_run_sync, "process", success, error_message, summary
        )


@router.post("/check")
async def trigger_check(
    container: ContainerDep,
    _auth: ApiKeyAuth,
    background_tasks: BackgroundTasks,
):
    """
    Trigger the check media use case.

    This endpoint replaces the cron job that runs `scruffy check`.
    Requires API key authentication via X-Api-Key header.

    The check runs in the background and returns immediately.
    """
    logger.info("Check task triggered via API")

    background_tasks.add_task(_run_check_task, container)

    return {
        "status": "started",
        "task": "check",
        "message": "Check task started in background",
    }


@router.post("/check/sync")
async def trigger_check_sync(
    container: ContainerDep,
    _auth: ApiKeyAuth,
):
    """
    Trigger the check media use case synchronously.

    This endpoint runs the check and waits for completion,
    returning the results. Useful for debugging or when you
    need to see the output immediately.

    Requires API key authentication via X-Api-Key header.
    """
    logger.info("Sync check task triggered via API")

    success = False
    error_message: str | None = None
    try:
        results = await container.check_media_requests_use_case.execute_with_retention(
            container.retention_calculator
        )
        success = True

        # Sort by days_left ascending
        results_sorted = sorted(results, key=lambda r: r.retention.days_left)

        # Convert to JSON-serializable format
        media_list = []
        for result in results_sorted:
            media_list.append({
                "request": result.request.json(),
                "media": {
                    "id": result.media.id,
                    "title": result.media.title,
                    "poster": result.media.poster,
                    "seasons": result.media.seasons,
                    "size_on_disk": result.media.size_on_disk,
                    "available_since": (
                        result.media.available_since.isoformat()
                        if result.media.available_since
                        else None
                    ),
                    "available": result.media.available,
                },
                "retention": asdict(result.retention),
            })

        logger.info(
            "Sync check task completed",
            extra={"results_count": len(media_list)},
        )

        return {
            "status": "completed",
            "task": "check",
            "results": media_list,
            "count": len(media_list),
        }

    except Exception as e:
        error_message = str(e)
        logger.error("Sync check task failed", extra={"error": str(e)})
        await asyncio.to_thread(
            record_job_run_sync, "check", False, error_message, None
        )
        return {
            "status": "failed",
            "task": "check",
            "error": str(e),
        }
    finally:
        if success:
            check_summary = {
                "items_checked": len(results),
                "needing_attention": sum(
                    1 for r in results if r.retention.remind or r.retention.delete
                ),
            }
            await asyncio.to_thread(
                record_job_run_sync, "check", True, None, check_summary
            )


@router.post("/process")
async def trigger_process(
    container: ContainerDep,
    _auth: ApiKeyAuth,
    background_tasks: BackgroundTasks,
):
    """
    Trigger the process media use case.

    This endpoint replaces the cron job that runs `scruffy process`.
    It will send reminders and delete media based on retention policy.

    Requires API key authentication via X-Api-Key header.

    The process runs in the background and returns immediately.
    """
    logger.info("Process task triggered via API")

    background_tasks.add_task(_run_process_task, container)

    return {
        "status": "started",
        "task": "process",
        "message": "Process task started in background",
    }


@router.post("/process/sync")
async def trigger_process_sync(
    container: ContainerDep,
    _auth: ApiKeyAuth,
):
    """
    Trigger the process media use case synchronously.

    This endpoint runs the process and waits for completion.
    Useful for debugging or when you need confirmation of completion.

    Requires API key authentication via X-Api-Key header.
    """
    logger.info("Sync process task triggered via API")

    success = False
    error_message: str | None = None
    summary = None
    try:
        summary = await container.process_media_use_case.execute()
        success = True

        logger.info("Sync process task completed")

        return {
            "status": "completed",
            "task": "process",
            "message": "Process task completed successfully",
        }

    except Exception as e:
        error_message = str(e)
        logger.error("Sync process task failed", extra={"error": str(e)})
        await asyncio.to_thread(
            record_job_run_sync, "process", False, error_message, None
        )
        return {
            "status": "failed",
            "task": "process",
            "error": str(e),
        }
    finally:
        if success:
            await asyncio.to_thread(
                record_job_run_sync, "process", True, None, summary
            )
