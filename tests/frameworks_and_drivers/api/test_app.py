"""Tests for FastAPI application factory."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from scruffy.frameworks_and_drivers.api.app import create_app


@pytest.fixture
def mock_container():
    """Create mock container for testing."""
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
    container.radarr_gateway = Mock()
    container.radarr_gateway.status = AsyncMock(return_value=True)
    container.sonarr_gateway = Mock()
    container.sonarr_gateway.status = AsyncMock(return_value=True)
    container.retention_calculator = Mock()
    return container


@pytest.fixture
def app_with_mock_container(mock_container):
    """Create app with mocked container."""
    with patch(
        "scruffy.frameworks_and_drivers.api.app.Container",
        return_value=mock_container,
    ):
        with patch("scruffy.frameworks_and_drivers.api.app.configure_logging"):
            app = create_app()
            # Manually set container since lifespan won't run in test
            app.state.container = mock_container
            yield app


@pytest.fixture
def client(app_with_mock_container):
    """Create test client."""
    return TestClient(app_with_mock_container)


class TestAppFactory:
    """Tests for create_app function."""

    def test_app_created_successfully(self, app_with_mock_container):
        """Test that app is created with correct attributes."""
        app = app_with_mock_container

        assert app.title == "Scruffy API"
        assert app.version == "0.3.2"

    def test_health_endpoint_exists(self, client):
        """Test that health endpoint is registered."""
        response = client.get("/health")

        # Should return 200 (health check doesn't require auth)
        assert response.status_code == 200


class TestHealthRoutes:
    """Tests for health check routes."""

    def test_health_check_healthy(self, client, mock_container):
        """Test health check when all services are healthy."""
        mock_container.overseer_gateway.status = AsyncMock(return_value=True)
        mock_container.radarr_gateway.status = AsyncMock(return_value=True)
        mock_container.sonarr_gateway.status = AsyncMock(return_value=True)

        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["services"]["overseerr"] == "healthy"
        assert data["services"]["radarr"] == "healthy"
        assert data["services"]["sonarr"] == "healthy"

    def test_health_check_degraded_overseerr(self, client, mock_container):
        """Test health check when Overseerr is unhealthy."""
        mock_container.overseer_gateway.status = AsyncMock(return_value=False)
        mock_container.radarr_gateway.status = AsyncMock(return_value=True)
        mock_container.sonarr_gateway.status = AsyncMock(return_value=True)

        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["services"]["overseerr"] == "unhealthy"
        assert data["services"]["radarr"] == "healthy"
        assert data["services"]["sonarr"] == "healthy"

    def test_health_check_degraded_radarr(self, client, mock_container):
        """Test health check when Radarr is unhealthy."""
        mock_container.overseer_gateway.status = AsyncMock(return_value=True)
        mock_container.radarr_gateway.status = AsyncMock(return_value=False)
        mock_container.sonarr_gateway.status = AsyncMock(return_value=True)

        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["services"]["radarr"] == "unhealthy"

    def test_health_check_degraded_sonarr(self, client, mock_container):
        """Test health check when Sonarr is unhealthy."""
        mock_container.overseer_gateway.status = AsyncMock(return_value=True)
        mock_container.radarr_gateway.status = AsyncMock(return_value=True)
        mock_container.sonarr_gateway.status = AsyncMock(return_value=False)

        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["services"]["sonarr"] == "unhealthy"
