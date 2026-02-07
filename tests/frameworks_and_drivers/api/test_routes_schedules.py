"""Tests for schedule routes (CRUD and run-now)."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from scruffy.frameworks_and_drivers.api.app import create_app
from scruffy.frameworks_and_drivers.api.auth import PlexUser, require_admin
from scruffy.frameworks_and_drivers.database.database import reset_engine_for_testing


@pytest.fixture
def mock_admin_user():
    """Create mock admin user for schedule routes."""
    return PlexUser(
        id=1,
        uuid="admin-uuid",
        username="admin",
        email="admin@example.com",
        thumb=None,
    )


@pytest.fixture
def mock_container():
    """Create mock container for schedule tests."""
    container = Mock()
    container.check_media_requests_use_case = Mock()
    container.check_media_requests_use_case.execute_with_retention = AsyncMock(
        return_value=[]
    )
    container.process_media_use_case = Mock()
    container.process_media_use_case.execute = AsyncMock(
        return_value={"reminders": [], "deletions": []}
    )
    container.overseer_gateway = Mock()
    container.overseer_gateway.status = AsyncMock(return_value=True)
    container.overseer_gateway.get_user_by_plex_id = AsyncMock(
        return_value={"permissions": 2}
    )
    container.radarr_gateway = Mock()
    container.radarr_gateway.status = AsyncMock(return_value=True)
    container.sonarr_gateway = Mock()
    container.sonarr_gateway.status = AsyncMock(return_value=True)
    container.retention_calculator = Mock()
    return container


@pytest.fixture
def app_with_schedule_db(mock_container):
    """Create app with mocked container and temp DB for schedules."""
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
                    mock_settings.api_port = 3000
                    mock_settings.api_enabled = True
                    mock_settings.cors_origins = None
                    app = create_app()
                    app.state.container = mock_container
                    yield app


@pytest.fixture
def client(app_with_schedule_db, mock_admin_user):
    """Create test client with admin auth override."""
    client = TestClient(app_with_schedule_db)

    async def override_require_admin():
        return mock_admin_user

    client.app.dependency_overrides[require_admin] = override_require_admin  # type: ignore[possibly-missing-attribute]
    yield client
    client.app.dependency_overrides.clear()  # type: ignore[possibly-missing-attribute]


class TestScheduleCrud:
    """Tests for schedule CRUD operations."""

    def test_list_schedules_empty(self, client):
        """Test listing schedules when none exist."""
        response = client.get("/api/admin/schedules")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_schedule(self, client):
        """Test creating a schedule."""
        response = client.post(
            "/api/admin/schedules",
            json={
                "job_type": "check",
                "cron_expression": "0 */6 * * *",
                "enabled": True,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["job_type"] == "check"
        assert data["cron_expression"] == "0 */6 * * *"
        assert data["enabled"] is True
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_schedule_process_type(self, client):
        """Test creating a process schedule."""
        response = client.post(
            "/api/admin/schedules",
            json={
                "job_type": "process",
                "cron_expression": "0 0 * * *",
                "enabled": True,
            },
        )
        assert response.status_code == 201
        assert response.json()["job_type"] == "process"

    def test_create_schedule_invalid_job_type(self, client):
        """Test creating schedule with invalid job_type fails."""
        response = client.post(
            "/api/admin/schedules",
            json={
                "job_type": "invalid",
                "cron_expression": "0 */6 * * *",
                "enabled": True,
            },
        )
        assert response.status_code == 422

    def test_create_schedule_invalid_cron(self, client):
        """Test creating schedule with too-short cron fails."""
        response = client.post(
            "/api/admin/schedules",
            json={
                "job_type": "check",
                "cron_expression": "short",
                "enabled": True,
            },
        )
        assert response.status_code == 422

    def test_get_schedule(self, client):
        """Test getting a single schedule by id."""
        create_resp = client.post(
            "/api/admin/schedules",
            json={
                "job_type": "check",
                "cron_expression": "0 */6 * * *",
                "enabled": True,
            },
        )
        schedule_id = create_resp.json()["id"]

        response = client.get(f"/api/admin/schedules/{schedule_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == schedule_id
        assert data["job_type"] == "check"

    def test_get_schedule_not_found(self, client):
        """Test getting non-existent schedule returns 404."""
        response = client.get("/api/admin/schedules/99999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_list_schedules_after_create(self, client):
        """Test listing schedules returns created entries."""
        client.post(
            "/api/admin/schedules",
            json={
                "job_type": "check",
                "cron_expression": "0 */6 * * *",
                "enabled": True,
            },
        )
        client.post(
            "/api/admin/schedules",
            json={
                "job_type": "process",
                "cron_expression": "0 0 * * *",
                "enabled": False,
            },
        )

        response = client.get("/api/admin/schedules")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["job_type"] == "check"
        assert data[1]["job_type"] == "process"
        assert data[1]["enabled"] is False

    def test_update_schedule(self, client):
        """Test updating a schedule."""
        create_resp = client.post(
            "/api/admin/schedules",
            json={
                "job_type": "check",
                "cron_expression": "0 */6 * * *",
                "enabled": True,
            },
        )
        schedule_id = create_resp.json()["id"]

        response = client.patch(
            f"/api/admin/schedules/{schedule_id}",
            json={
                "job_type": "process",
                "cron_expression": "0 12 * * *",
                "enabled": False,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["job_type"] == "process"
        assert data["cron_expression"] == "0 12 * * *"
        assert data["enabled"] is False

    def test_update_schedule_partial(self, client):
        """Test partial update of schedule (only enabled)."""
        create_resp = client.post(
            "/api/admin/schedules",
            json={
                "job_type": "check",
                "cron_expression": "0 */6 * * *",
                "enabled": True,
            },
        )
        schedule_id = create_resp.json()["id"]

        response = client.patch(
            f"/api/admin/schedules/{schedule_id}",
            json={"enabled": False},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is False
        assert data["job_type"] == "check"
        assert data["cron_expression"] == "0 */6 * * *"

    def test_delete_schedule(self, client):
        """Test deleting a schedule."""
        create_resp = client.post(
            "/api/admin/schedules",
            json={
                "job_type": "check",
                "cron_expression": "0 */6 * * *",
                "enabled": True,
            },
        )
        schedule_id = create_resp.json()["id"]

        response = client.delete(f"/api/admin/schedules/{schedule_id}")
        assert response.status_code == 204

        get_resp = client.get(f"/api/admin/schedules/{schedule_id}")
        assert get_resp.status_code == 404

    def test_delete_schedule_not_found(self, client):
        """Test deleting non-existent schedule returns 404."""
        response = client.delete("/api/admin/schedules/99999")
        assert response.status_code == 404

    def test_create_schedule_duplicate_job_type_returns_409(self, client):
        """Test creating second schedule with same job_type returns 409."""
        client.post(
            "/api/admin/schedules",
            json={
                "job_type": "check",
                "cron_expression": "0 */6 * * *",
                "enabled": True,
            },
        )
        response = client.post(
            "/api/admin/schedules",
            json={
                "job_type": "check",
                "cron_expression": "0 0 * * *",
                "enabled": True,
            },
        )
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()

    def test_update_schedule_to_duplicate_job_type_returns_409(self, client):
        """Test updating schedule to change job_type to one already used returns 409."""
        client.post(
            "/api/admin/schedules",
            json={
                "job_type": "check",
                "cron_expression": "0 */6 * * *",
                "enabled": True,
            },
        )
        process_resp = client.post(
            "/api/admin/schedules",
            json={
                "job_type": "process",
                "cron_expression": "0 0 * * *",
                "enabled": True,
            },
        )
        process_id = process_resp.json()["id"]
        # Try to change process schedule to check (already exists)
        response = client.patch(
            f"/api/admin/schedules/{process_id}",
            json={"job_type": "check"},
        )
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()

    def test_update_schedule_same_job_type_succeeds(self, client):
        """Test updating schedule with same job_type (no change) succeeds."""
        create_resp = client.post(
            "/api/admin/schedules",
            json={
                "job_type": "check",
                "cron_expression": "0 */6 * * *",
                "enabled": True,
            },
        )
        schedule_id = create_resp.json()["id"]

        response = client.patch(
            f"/api/admin/schedules/{schedule_id}",
            json={"job_type": "check", "enabled": False},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["job_type"] == "check"
        assert data["enabled"] is False

    def test_update_schedule_to_unused_job_type_succeeds(self, client):
        """Test updating schedule to change job_type to unused type succeeds."""
        create_resp = client.post(
            "/api/admin/schedules",
            json={
                "job_type": "check",
                "cron_expression": "0 */6 * * *",
                "enabled": True,
            },
        )
        schedule_id = create_resp.json()["id"]

        response = client.patch(
            f"/api/admin/schedules/{schedule_id}",
            json={"job_type": "process"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["job_type"] == "process"


class TestScheduleAuth:
    """Tests for schedule route authentication."""

    def test_list_schedules_unauthenticated_returns_401(
        self, app_with_schedule_db, mock_admin_user
    ):
        """Test that unauthenticated request returns 401."""
        client = TestClient(app_with_schedule_db)
        # No override - require_admin will fail without session
        response = client.get("/api/admin/schedules")
        assert response.status_code == 401


class TestRunScheduleNow:
    """Tests for POST /api/admin/schedules/{id}/run."""

    def test_run_schedule_now_check_calls_use_case(self, client, mock_container):
        """Test run-now for check schedule calls execute_with_retention."""
        create_resp = client.post(
            "/api/admin/schedules",
            json={
                "job_type": "check",
                "cron_expression": "0 */6 * * *",
                "enabled": True,
            },
        )
        schedule_id = create_resp.json()["id"]

        response = client.post(f"/api/admin/schedules/{schedule_id}/run")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "started"
        assert data["job_type"] == "check"

        # Background task runs - with TestClient we need to allow it to complete
        # TestClient runs background tasks after request
        mock_container.check_media_requests_use_case.execute_with_retention.assert_called_once_with(
            mock_container.retention_calculator
        )
        mock_container.process_media_use_case.execute.assert_not_called()

    def test_run_schedule_now_process_calls_use_case(self, client, mock_container):
        """Test run-now for process schedule calls execute."""
        create_resp = client.post(
            "/api/admin/schedules",
            json={
                "job_type": "process",
                "cron_expression": "0 0 * * *",
                "enabled": True,
            },
        )
        schedule_id = create_resp.json()["id"]

        response = client.post(f"/api/admin/schedules/{schedule_id}/run")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "started"
        assert data["job_type"] == "process"

        mock_container.process_media_use_case.execute.assert_called_once()
        mock_container.check_media_requests_use_case.execute_with_retention.assert_not_called()

    def test_run_schedule_now_not_found(self, client):
        """Test run-now for non-existent schedule returns 404."""
        response = client.post("/api/admin/schedules/99999/run")
        assert response.status_code == 404

    def test_run_schedule_now_logs_completion(self, client, mock_container, caplog):
        """Test that run-now logs when job completes."""
        import logging

        caplog.set_level(logging.INFO)
        create_resp = client.post(
            "/api/admin/schedules",
            json={
                "job_type": "check",
                "cron_expression": "0 */6 * * *",
                "enabled": True,
            },
        )
        schedule_id = create_resp.json()["id"]

        client.post(f"/api/admin/schedules/{schedule_id}/run")

        assert any(
            "Run-now job completed" in rec.message
            for rec in caplog.records
            if rec.name == "scruffy.frameworks_and_drivers.api.routes.schedules"
        )
