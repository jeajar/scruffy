"""Tests for admin job runs route."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from scruffy.frameworks_and_drivers.api.app import create_app
from scruffy.frameworks_and_drivers.api.auth import PlexUser, require_admin
from scruffy.frameworks_and_drivers.database.database import reset_engine_for_testing
from scruffy.frameworks_and_drivers.database.job_run_store import record_job_run_sync


@pytest.fixture
def mock_admin_user():
    """Create mock admin user for jobs routes."""
    return PlexUser(
        id=1,
        uuid="admin-uuid",
        username="admin",
        email="admin@example.com",
        thumb=None,
    )


@pytest.fixture
def mock_container():
    """Create mock container for jobs tests."""
    container = Mock()
    container.overseer_gateway = Mock()
    container.overseer_gateway.status = AsyncMock(return_value=True)
    container.radarr_gateway = Mock()
    container.radarr_gateway.status = AsyncMock(return_value=True)
    container.sonarr_gateway = Mock()
    container.sonarr_gateway.status = AsyncMock(return_value=True)
    return container


@pytest.fixture
def app_with_jobs_db(mock_container):
    """Create app with mocked container and temp DB for job runs."""
    reset_engine_for_testing()
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        with patch(
            "scruffy.frameworks_and_drivers.api.app.Container",
            return_value=mock_container,
        ):
            with patch("scruffy.frameworks_and_drivers.api.app.configure_logging"):
                with patch(
                    "scruffy.frameworks_and_drivers.database.database.settings"
                ) as mock_settings:
                    mock_settings.data_dir = data_dir
                    mock_settings.api_secret_key = "test-secret"
                    mock_settings.overseerr_url = "http://test"
                    mock_settings.overseerr_api_key = "test-key"
                    mock_settings.radarr_url = "http://test"
                    mock_settings.radarr_api_key = "test-key"
                    mock_settings.sonarr_url = "http://test"
                    mock_settings.sonarr_api_key = "test-key"
                    mock_settings.retention_days = 30
                    mock_settings.reminder_days = 7
                    mock_settings.log_level = "INFO"
                    mock_settings.log_file = None
                    mock_settings.loki_enabled = False
                    mock_settings.loki_url = None
                    mock_settings.loki_labels = None
                    mock_settings.api_host = "0.0.0.0"
                    mock_settings.api_port = 8000
                    mock_settings.api_enabled = True
                    mock_settings.cors_origins = None
                    app = create_app()
                    app.state.container = mock_container
                    yield app


@pytest.fixture
def client(app_with_jobs_db, mock_admin_user):
    """Create test client with admin auth override."""
    client = TestClient(app_with_jobs_db)

    async def override_require_admin():
        return mock_admin_user

    client.app.dependency_overrides[require_admin] = override_require_admin  # type: ignore[possibly-missing-attribute]
    yield client
    client.app.dependency_overrides.clear()  # type: ignore[possibly-missing-attribute]


class TestListJobRuns:
    """Tests for GET /api/admin/jobs."""

    def test_list_job_runs_empty(self, client):
        """Test GET returns empty list when no runs."""
        response = client.get("/api/admin/jobs")

        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_list_job_runs_returns_summary_when_present(self, client):
        """Test GET returns job runs with summary when stored."""
        summary = {
            "reminders": [
                {"email": "u@example.com", "title": "Some Movie", "days_left": 5}
            ],
            "deletions": [{"email": "u@example.com", "title": "Old Movie"}],
        }
        record_job_run_sync("process", True, None, summary)

        response = client.get("/api/admin/jobs")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        run = data[0]
        assert run["job_type"] == "process"
        assert run["success"] is True
        assert run["summary"] is not None
        assert run["summary"]["reminders"] == summary["reminders"]
        assert run["summary"]["deletions"] == summary["deletions"]

    def test_list_job_runs_returns_null_summary_when_not_stored(self, client):
        """Test GET returns summary null for runs recorded without summary."""
        record_job_run_sync("check", True, None)

        response = client.get("/api/admin/jobs")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0].get("summary") is None
