"""Tests for task routes."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from scruffy.domain.value_objects.media_status import MediaStatus
from scruffy.domain.value_objects.request_status import RequestStatus
from scruffy.frameworks_and_drivers.api.app import create_app
from scruffy.use_cases.dtos.media_check_result_dto import (
    MediaCheckResultDTO,
    RetentionResultDTO,
)
from scruffy.use_cases.dtos.media_info_dto import MediaInfoDTO
from scruffy.use_cases.dtos.request_dto import RequestDTO


@pytest.fixture
def sample_media_check_result():
    """Create sample media check result."""
    request_dto = RequestDTO(
        user_id=1,
        user_email="test@example.com",
        type="movie",
        request_id=1,
        request_status=RequestStatus.APPROVED,
        updated_at=datetime.now(UTC) - timedelta(days=25),
        media_status=MediaStatus.AVAILABLE,
        media_id=99,
        external_service_id=101,
        seasons=[],
    )
    media_dto = MediaInfoDTO(
        id=1,
        title="Test Movie",
        available=True,
        available_since=datetime.now(UTC) - timedelta(days=25),
        size_on_disk=1000000,
        poster="http://example.com/poster.jpg",
        seasons=[],
    )
    retention_dto = RetentionResultDTO(remind=False, delete=False, days_left=5)

    return MediaCheckResultDTO(
        request=request_dto,
        media=media_dto,
        retention=retention_dto,
    )


@pytest.fixture
def mock_container(sample_media_check_result):
    """Create mock container for testing."""
    container = Mock()
    container.check_media_requests_use_case = Mock()
    container.check_media_requests_use_case.execute_with_retention = AsyncMock(
        return_value=[sample_media_check_result]
    )
    container.process_media_use_case = Mock()
    container.process_media_use_case.execute = AsyncMock(
        return_value={"reminders": [], "deletions": []}
    )
    container.overseer_gateway = Mock()
    container.overseer_gateway.status = AsyncMock(return_value=True)
    container.retention_calculator = Mock()
    return container


@pytest.fixture
def app_with_mock_container(mock_container):
    """Create app with mocked container and patched record_job_run_sync (no real DB)."""
    with patch(
        "scruffy.frameworks_and_drivers.api.app.Container",
        return_value=mock_container,
    ):
        with patch("scruffy.frameworks_and_drivers.api.app.configure_logging"):
            with patch(
                "scruffy.frameworks_and_drivers.api.routes.tasks.record_job_run_sync"
            ):
                app = create_app()
                app.state.container = mock_container
                yield app


@pytest.fixture
def client(app_with_mock_container):
    """Create test client."""
    return TestClient(app_with_mock_container)


class TestCheckTask:
    """Tests for POST /api/tasks/check endpoint."""

    def test_no_api_key_returns_401(self, client):
        """Test that missing API key returns 401."""
        response = client.post("/api/tasks/check")

        assert response.status_code == 401

    def test_invalid_api_key_returns_401(self, client):
        """Test that invalid API key returns 401."""
        with patch(
            "scruffy.frameworks_and_drivers.api.auth.get_overseerr_api_key",
            return_value="valid-key",
        ):
            response = client.post(
                "/api/tasks/check", headers={"X-Api-Key": "invalid-key"}
            )

            assert response.status_code == 401

    def test_valid_api_key_starts_task(self, client, mock_container):
        """Test that valid API key starts background task."""
        with patch(
            "scruffy.frameworks_and_drivers.api.auth.get_overseerr_api_key",
            return_value="valid-key",
        ):
            response = client.post(
                "/api/tasks/check", headers={"X-Api-Key": "valid-key"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "started"
            assert data["task"] == "check"


class TestCheckSyncTask:
    """Tests for POST /api/tasks/check/sync endpoint."""

    def test_no_api_key_returns_401(self, client):
        """Test that missing API key returns 401."""
        response = client.post("/api/tasks/check/sync")

        assert response.status_code == 401

    def test_valid_api_key_runs_check_and_returns_results(
        self, client, mock_container
    ):
        """Test that valid API key runs check and returns results."""
        with patch(
            "scruffy.frameworks_and_drivers.api.auth.get_overseerr_api_key",
            return_value="valid-key",
        ):
            response = client.post(
                "/api/tasks/check/sync", headers={"X-Api-Key": "valid-key"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "completed"
            assert data["task"] == "check"
            assert "results" in data
            assert data["count"] == 1
            assert data["results"][0]["media"]["title"] == "Test Movie"

    def test_check_failure_returns_error(self, client, mock_container):
        """Test that check failure returns error status."""
        mock_container.check_media_requests_use_case.execute_with_retention = (
            AsyncMock(side_effect=Exception("Test error"))
        )

        with patch(
            "scruffy.frameworks_and_drivers.api.auth.get_overseerr_api_key",
            return_value="valid-key",
        ):
            response = client.post(
                "/api/tasks/check/sync", headers={"X-Api-Key": "valid-key"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "failed"
            assert "error" in data


class TestProcessTask:
    """Tests for POST /api/tasks/process endpoint."""

    def test_no_api_key_returns_401(self, client):
        """Test that missing API key returns 401."""
        response = client.post("/api/tasks/process")

        assert response.status_code == 401

    def test_valid_api_key_starts_task(self, client, mock_container):
        """Test that valid API key starts background task."""
        with patch(
            "scruffy.frameworks_and_drivers.api.auth.get_overseerr_api_key",
            return_value="valid-key",
        ):
            response = client.post(
                "/api/tasks/process", headers={"X-Api-Key": "valid-key"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "started"
            assert data["task"] == "process"


class TestProcessSyncTask:
    """Tests for POST /api/tasks/process/sync endpoint."""

    def test_no_api_key_returns_401(self, client):
        """Test that missing API key returns 401."""
        response = client.post("/api/tasks/process/sync")

        assert response.status_code == 401

    def test_valid_api_key_runs_process(self, client, mock_container):
        """Test that valid API key runs process and returns success."""
        with patch(
            "scruffy.frameworks_and_drivers.api.auth.get_overseerr_api_key",
            return_value="valid-key",
        ):
            response = client.post(
                "/api/tasks/process/sync", headers={"X-Api-Key": "valid-key"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "completed"
            assert data["task"] == "process"

            mock_container.process_media_use_case.execute.assert_called_once()

    def test_process_failure_returns_error(self, client, mock_container):
        """Test that process failure returns error status."""
        mock_container.process_media_use_case.execute = AsyncMock(
            side_effect=Exception("Process error")
        )

        with patch(
            "scruffy.frameworks_and_drivers.api.auth.get_overseerr_api_key",
            return_value="valid-key",
        ):
            response = client.post(
                "/api/tasks/process/sync", headers={"X-Api-Key": "valid-key"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "failed"
            assert "error" in data
