"""Tests for background scheduler (schedule job execution and logging)."""

import logging
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from scruffy.frameworks_and_drivers.api.scheduler import (
    add_job_to_scheduler,
    remove_job_from_scheduler,
    start_scheduler,
    update_job_in_scheduler,
)
from scruffy.frameworks_and_drivers.database.database import reset_engine_for_testing
from scruffy.frameworks_and_drivers.database.schedule_model import ScheduleJobModel


@pytest.fixture
def mock_container():
    """Create mock container for scheduler tests."""
    container = Mock()
    container.check_media_requests_use_case = Mock()
    container.check_media_requests_use_case.execute_with_retention = AsyncMock(
        return_value=[]
    )
    container.process_media_use_case = Mock()
    container.process_media_use_case.execute = AsyncMock(
        return_value={"reminders": [], "deletions": []}
    )
    container.retention_calculator = Mock()
    return container


@pytest.fixture
def mock_app(mock_container):
    """Create mock FastAPI app with container."""
    app = Mock()
    app.state = Mock()
    app.state.container = mock_container
    return app


@pytest.fixture
def schedule_db_with_temp_dir():
    """Provide temp dir for schedule DB (get_engine uses settings.data_dir)."""
    reset_engine_for_testing()
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch(
            "scruffy.frameworks_and_drivers.database.database.settings"
        ) as mock_settings:
            mock_settings.data_dir = Path(tmpdir)
            yield mock_settings


class TestSchedulerJobExecution:
    """Tests that scheduled jobs run and call correct methods."""

    @pytest.mark.asyncio
    async def test_scheduler_check_job_calls_execute_with_retention(
        self, mock_app, mock_container, schedule_db_with_temp_dir
    ):
        """Test that a check schedule job calls execute_with_retention."""
        start_scheduler(mock_app)
        model = ScheduleJobModel(
            id=1,
            job_type="check",
            cron_expression="0 */6 * * *",
            enabled=True,
        )
        add_job_to_scheduler(mock_app, model)

        scheduler: AsyncIOScheduler = mock_app.state.scheduler
        jobs = scheduler.get_jobs()
        assert len(jobs) == 1
        job = jobs[0]
        await job.func()

        mock_container.check_media_requests_use_case.execute_with_retention.assert_called_once_with(
            mock_container.retention_calculator
        )
        mock_container.process_media_use_case.execute.assert_not_called()

        scheduler.shutdown(wait=False)

    @pytest.mark.asyncio
    async def test_scheduler_process_job_calls_execute(
        self, mock_app, mock_container, schedule_db_with_temp_dir
    ):
        """Test that a process schedule job calls execute."""
        start_scheduler(mock_app)
        model = ScheduleJobModel(
            id=2,
            job_type="process",
            cron_expression="0 0 * * *",
            enabled=True,
        )
        add_job_to_scheduler(mock_app, model)

        scheduler: AsyncIOScheduler = mock_app.state.scheduler
        jobs = scheduler.get_jobs()
        assert len(jobs) == 1
        job = jobs[0]
        await job.func()

        mock_container.process_media_use_case.execute.assert_called_once()
        mock_container.check_media_requests_use_case.execute_with_retention.assert_not_called()

        scheduler.shutdown(wait=False)


class TestSchedulerLogging:
    """Tests that scheduler logs when jobs run."""

    @pytest.mark.asyncio
    async def test_scheduler_check_job_logs_completion(
        self, mock_app, mock_container, schedule_db_with_temp_dir, caplog
    ):
        """Test that scheduled check job logs completion."""
        caplog.set_level(logging.INFO)
        start_scheduler(mock_app)
        model = ScheduleJobModel(
            id=1,
            job_type="check",
            cron_expression="0 */6 * * *",
            enabled=True,
        )
        add_job_to_scheduler(mock_app, model)

        scheduler: AsyncIOScheduler = mock_app.state.scheduler
        job = scheduler.get_jobs()[0]
        await job.func()

        assert any(
            "Scheduled check job completed" in rec.message
            for rec in caplog.records
            if rec.name == "scruffy.frameworks_and_drivers.api.scheduler"
        )

        scheduler.shutdown(wait=False)

    @pytest.mark.asyncio
    async def test_scheduler_process_job_logs_completion(
        self, mock_app, mock_container, schedule_db_with_temp_dir, caplog
    ):
        """Test that scheduled process job logs completion."""
        caplog.set_level(logging.INFO)
        start_scheduler(mock_app)
        model = ScheduleJobModel(
            id=2,
            job_type="process",
            cron_expression="0 0 * * *",
            enabled=True,
        )
        add_job_to_scheduler(mock_app, model)

        scheduler: AsyncIOScheduler = mock_app.state.scheduler
        job = scheduler.get_jobs()[0]
        await job.func()

        assert any(
            "Scheduled process job completed" in rec.message
            for rec in caplog.records
            if rec.name == "scruffy.frameworks_and_drivers.api.scheduler"
        )

        scheduler.shutdown(wait=False)


class TestSchedulerAddRemoveUpdate:
    """Tests for add/remove/update job in scheduler."""

    def test_add_job_to_scheduler_when_scheduler_missing(self, mock_app):
        """Test add_job_to_scheduler returns early when no scheduler."""
        mock_app.state.scheduler = None
        model = ScheduleJobModel(
            id=1,
            job_type="check",
            cron_expression="0 */6 * * *",
            enabled=True,
        )
        add_job_to_scheduler(mock_app, model)
        # Should not raise

    @pytest.mark.asyncio
    async def test_remove_job_from_scheduler(self, mock_app, schedule_db_with_temp_dir):
        """Test remove_job_from_scheduler removes the job."""
        start_scheduler(mock_app)
        model = ScheduleJobModel(
            id=1,
            job_type="check",
            cron_expression="0 */6 * * *",
            enabled=True,
        )
        add_job_to_scheduler(mock_app, model)
        assert len(mock_app.state.scheduler.get_jobs()) == 1

        remove_job_from_scheduler(mock_app, 1)
        assert len(mock_app.state.scheduler.get_jobs()) == 0

        mock_app.state.scheduler.shutdown(wait=False)

    @pytest.mark.asyncio
    async def test_update_job_in_scheduler(
        self, mock_app, mock_container, schedule_db_with_temp_dir
    ):
        """Test update_job_in_scheduler replaces the job."""
        start_scheduler(mock_app)
        model = ScheduleJobModel(
            id=1,
            job_type="check",
            cron_expression="0 */6 * * *",
            enabled=True,
        )
        add_job_to_scheduler(mock_app, model)
        assert len(mock_app.state.scheduler.get_jobs()) == 1

        model.job_type = "process"
        model.cron_expression = "0 12 * * *"
        update_job_in_scheduler(mock_app, model)
        jobs = mock_app.state.scheduler.get_jobs()
        assert len(jobs) == 1
        # Job should be updated (same id, different config)
        assert jobs[0].id == "schedule-1"

        mock_app.state.scheduler.shutdown(wait=False)
