"""Tests for media routes."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from scruffy.domain.value_objects.media_status import MediaStatus
from scruffy.domain.value_objects.request_status import RequestStatus
from scruffy.frameworks_and_drivers.api.app import create_app
from scruffy.frameworks_and_drivers.api.auth import PlexUser, get_current_user
from scruffy.frameworks_and_drivers.api.routes.media import invalidate_media_list_cache
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
    retention_dto = RetentionResultDTO(
        remind=False, delete=False, days_left=5, reminder_sent=False
    )

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
    container.overseer_gateway = Mock()
    container.overseer_gateway.status = AsyncMock(return_value=True)
    container.retention_calculator = Mock()
    return container


@pytest.fixture
def mock_authenticated_user():
    """Create mock authenticated user."""
    return PlexUser(
        id=1,
        uuid="abc-123",
        email="test@example.com",
        username="testuser",
        thumb="http://example.com/avatar.jpg",
    )


@pytest.fixture
def app_with_mock_container(mock_container):
    """Create app with mocked container."""
    with patch(
        "scruffy.frameworks_and_drivers.api.app.Container",
        return_value=mock_container,
    ):
        with patch("scruffy.frameworks_and_drivers.api.app.configure_logging"):
            app = create_app()
            app.state.container = mock_container
            yield app


@pytest.fixture
def client(app_with_mock_container):
    """Create test client."""
    return TestClient(app_with_mock_container)


class TestGetMediaList:
    """Tests for GET /api/media endpoint."""

    def test_unauthenticated_returns_401(self, client):
        """Test that unauthenticated request returns 401."""
        response = client.get("/api/media")

        assert response.status_code == 401

    def test_authenticated_returns_media_list(
        self, client, mock_container, mock_authenticated_user
    ):
        """Test that authenticated request returns media list."""

        async def override_get_current_user():
            return mock_authenticated_user

        client.app.dependency_overrides[get_current_user] = override_get_current_user

        response = client.get("/api/media")

        assert response.status_code == 200
        data = response.json()
        assert "media" in data
        assert "count" in data
        assert data["count"] == 1
        assert data["media"][0]["media"]["title"] == "Test Movie"

        client.app.dependency_overrides.clear()

    def test_media_list_sorted_by_days_left(
        self, client, mock_container, mock_authenticated_user
    ):
        """Test that media list is sorted by days_left ascending."""
        invalidate_media_list_cache()
        # Create multiple results with different days_left
        results = []
        for days_left in [10, 5, 15, 2]:
            request_dto = RequestDTO(
                user_id=1,
                user_email="test@example.com",
                type="movie",
                request_id=days_left,
                request_status=RequestStatus.APPROVED,
                updated_at=datetime.now(UTC),
                media_status=MediaStatus.AVAILABLE,
                media_id=days_left,
                external_service_id=days_left,
                seasons=[],
            )
            media_dto = MediaInfoDTO(
                id=days_left,
                title=f"Movie {days_left}",
                available=True,
                available_since=datetime.now(UTC) - timedelta(days=30 - days_left),
                size_on_disk=1000000,
                poster="",
                seasons=[],
            )
            retention_dto = RetentionResultDTO(
                remind=False, delete=False, days_left=days_left
            )
            results.append(
                MediaCheckResultDTO(
                    request=request_dto, media=media_dto, retention=retention_dto
                )
            )

        mock_container.check_media_requests_use_case.execute_with_retention = AsyncMock(
            return_value=results
        )

        async def override_get_current_user():
            return mock_authenticated_user

        client.app.dependency_overrides[get_current_user] = override_get_current_user

        response = client.get("/api/media")

        assert response.status_code == 200
        data = response.json()

        # Verify sorted by days_left ascending
        days_left_values = [item["retention"]["days_left"] for item in data["media"]]
        assert days_left_values == [2, 5, 10, 15]

        client.app.dependency_overrides.clear()

    def test_media_list_includes_reminder_sent_in_retention(
        self, client, mock_container, mock_authenticated_user, sample_media_check_result
    ):
        """Test that retention in API response includes reminder_sent."""
        invalidate_media_list_cache()
        result_with_reminder = MediaCheckResultDTO(
            request=sample_media_check_result.request,
            media=sample_media_check_result.media,
            retention=RetentionResultDTO(
                remind=True, delete=False, days_left=5, reminder_sent=True
            ),
        )
        mock_container.check_media_requests_use_case.execute_with_retention = AsyncMock(
            return_value=[result_with_reminder]
        )

        async def override_get_current_user():
            return mock_authenticated_user

        client.app.dependency_overrides[get_current_user] = override_get_current_user

        response = client.get("/api/media")

        assert response.status_code == 200
        data = response.json()
        assert "media" in data
        assert len(data["media"]) == 1
        assert "reminder_sent" in data["media"][0]["retention"]
        assert data["media"][0]["retention"]["reminder_sent"] is True

        client.app.dependency_overrides.clear()
