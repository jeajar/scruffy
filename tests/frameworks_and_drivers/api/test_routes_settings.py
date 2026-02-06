"""Tests for admin settings routes."""

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
    """Create mock admin user for settings routes."""
    return PlexUser(
        id=1,
        uuid="admin-uuid",
        username="admin",
        email="admin@example.com",
        thumb=None,
    )


@pytest.fixture
def mock_container():
    """Create mock container for settings tests."""
    container = Mock()
    container.overseer_gateway = Mock()
    container.overseer_gateway.status = AsyncMock(return_value=True)
    container.radarr_gateway = Mock()
    container.radarr_gateway.status = AsyncMock(return_value=True)
    container.sonarr_gateway = Mock()
    container.sonarr_gateway.status = AsyncMock(return_value=True)
    return container


@pytest.fixture
def app_with_settings_db(mock_container):
    """Create app with mocked container and temp DB for settings."""
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
                ) as mock_settings, patch(
                    "scruffy.frameworks_and_drivers.database.settings_store.settings"
                ) as store_mock:
                    for mock_obj in (mock_settings, store_mock):
                        mock_obj.data_dir = str(data_dir)
                        mock_obj.api_secret_key = "test-secret"
                        mock_obj.overseerr_url = "http://test"
                        mock_obj.overseerr_api_key = "test-key"
                        mock_obj.radarr_url = "http://test"
                        mock_obj.radarr_api_key = "test-key"
                        mock_obj.sonarr_url = "http://test"
                        mock_obj.sonarr_api_key = "test-key"
                        mock_obj.retention_days = 30
                        mock_obj.reminder_days = 7
                        mock_obj.email_enabled = False
                        mock_obj.smtp_host = "localhost"
                        mock_obj.smtp_port = 25
                        mock_obj.smtp_username = None
                        mock_obj.smtp_password = None
                        mock_obj.smtp_from_email = "test@example.com"
                        mock_obj.smtp_ssl_tls = True
                        mock_obj.smtp_starttls = False
                        mock_obj.extension_days = 7
                        mock_obj.log_level = "INFO"
                        mock_obj.log_file = None
                        mock_obj.loki_enabled = False
                        mock_obj.loki_url = None
                        mock_obj.loki_labels = None
                        mock_obj.api_host = "0.0.0.0"
                        mock_obj.api_port = 8000
                        mock_obj.api_enabled = True
                        mock_obj.cors_origins = None
                    app = create_app()
                    app.state.container = mock_container
                    yield app


@pytest.fixture
def client(app_with_settings_db, mock_admin_user):
    """Create test client with admin auth override."""
    client = TestClient(app_with_settings_db)

    async def override_require_admin():
        return mock_admin_user

    client.app.dependency_overrides[require_admin] = override_require_admin
    yield client
    client.app.dependency_overrides.clear()


class TestSettingsGet:
    """Tests for GET /api/admin/settings."""

    def test_get_settings_returns_full_shape(self, client):
        """Test GET returns retention_days, reminder_days, extension_days, services, and notifications."""
        response = client.get("/api/admin/settings")

        assert response.status_code == 200
        data = response.json()
        assert "retention_days" in data
        assert "reminder_days" in data
        assert "extension_days" in data
        assert "services" in data
        assert "notifications" in data
        assert "overseerr" in data["services"]
        assert "radarr" in data["services"]
        assert "sonarr" in data["services"]
        assert data["services"]["overseerr"]["url"] == "http://test"
        assert data["services"]["overseerr"]["api_key_set"] is True
        assert "email" in data["notifications"]
        assert data["notifications"]["email"]["enabled"] is False


class TestSettingsPatch:
    """Tests for PATCH /api/admin/settings."""

    def test_patch_extension_days(self, client):
        """Test PATCH updates extension_days."""
        response = client.patch(
            "/api/admin/settings",
            json={"extension_days": 14},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["extension_days"] == 14

    def test_patch_retention_days(self, client):
        """Test PATCH updates retention_days and reminder_days."""
        response = client.patch(
            "/api/admin/settings",
            json={"retention_days": 45, "reminder_days": 10},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["retention_days"] == 45
        assert data["reminder_days"] == 10


class TestSettingsTestService:
    """Tests for POST /api/admin/settings/services/test/{service}."""

    def test_test_overseerr_success(self, client, mock_container):
        """Test service test endpoint returns ok when gateway succeeds."""
        mock_container.overseer_gateway.status = AsyncMock(return_value=True)

        response = client.post(
            "/api/admin/settings/services/test/overseerr",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "overseerr"
        assert data["status"] == "ok"

    def test_test_overseerr_failure(self, client, mock_container):
        """Test service test endpoint returns failed when gateway fails."""
        mock_container.overseer_gateway.status = AsyncMock(return_value=False)

        response = client.post(
            "/api/admin/settings/services/test/overseerr",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"

    def test_test_unknown_service_returns_400(self, client):
        """Test unknown service returns 400."""
        response = client.post(
            "/api/admin/settings/services/test/unknown",
        )

        assert response.status_code == 400
