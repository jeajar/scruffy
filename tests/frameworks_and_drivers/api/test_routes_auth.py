"""Tests for auth routes (callback and check-pin with Overseerr user check)."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from scruffy.frameworks_and_drivers.api.app import create_app
from scruffy.frameworks_and_drivers.api.auth import PlexUser


@pytest.fixture
def plex_user():
    """Sample Plex user."""
    return PlexUser(
        id=42,
        uuid="plex-uuid-123",
        username="testuser",
        email="test@example.com",
        thumb="http://example.com/thumb.jpg",
    )


@pytest.fixture
def mock_container(plex_user):
    """Mock container with overseer_gateway.user_imported_by_plex_id."""
    container = Mock()
    container.overseer_gateway = Mock()
    container.overseer_gateway.user_imported_by_plex_id = AsyncMock(return_value=True)
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
            app.state.container = mock_container
            yield app


@pytest.fixture
def client(app_with_mock_container):
    """Create test client."""
    return TestClient(app_with_mock_container)


class TestAuthCallback:
    """Tests for GET /auth/callback."""

    def test_callback_redirects_when_pin_not_claimed(self, client, mock_container):
        """When PIN not claimed, redirect to login with error=not_claimed."""
        with patch(
            "scruffy.frameworks_and_drivers.api.routes.auth.check_plex_pin",
            new_callable=AsyncMock,
            return_value=None,
        ):
            response = client.get("/auth/callback?pin_id=123", follow_redirects=False)
        assert response.status_code == 302
        assert "not_claimed" in response.headers["location"]
        mock_container.overseer_gateway.user_imported_by_plex_id.assert_not_called()

    def test_callback_redirects_when_user_not_imported_in_overseerr(
        self, client, mock_container, plex_user
    ):
        """When user is not imported in Overseerr, redirect with error=not_imported."""
        mock_container.overseer_gateway.user_imported_by_plex_id = AsyncMock(
            return_value=False
        )
        with patch(
            "scruffy.frameworks_and_drivers.api.routes.auth.check_plex_pin",
            new_callable=AsyncMock,
            return_value=plex_user,
        ):
            response = client.get("/auth/callback?pin_id=123", follow_redirects=False)
        assert response.status_code == 302
        assert "not_imported" in response.headers["location"]
        mock_container.overseer_gateway.user_imported_by_plex_id.assert_called_once_with(
            42
        )

    def test_callback_creates_session_when_user_imported(
        self, client, mock_container, plex_user
    ):
        """When user is imported in Overseerr, create session and redirect to close page."""
        with patch(
            "scruffy.frameworks_and_drivers.api.routes.auth.check_plex_pin",
            new_callable=AsyncMock,
            return_value=plex_user,
        ):
            response = client.get("/auth/callback?pin_id=123", follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["location"] == "/auth/close"
        assert "scruffy_session" in response.headers.get("set-cookie", "")
        mock_container.overseer_gateway.user_imported_by_plex_id.assert_called_once_with(
            42
        )

    def test_callback_502_when_overseerr_check_fails(
        self, client, mock_container, plex_user
    ):
        """When Overseerr user check raises, return 502."""
        mock_container.overseer_gateway.user_imported_by_plex_id = AsyncMock(
            side_effect=Exception("Overseerr unreachable")
        )
        with patch(
            "scruffy.frameworks_and_drivers.api.routes.auth.check_plex_pin",
            new_callable=AsyncMock,
            return_value=plex_user,
        ):
            response = client.get("/auth/callback?pin_id=123")
        assert response.status_code == 502
        assert "verify server access" in response.json().get("detail", "")


class TestCheckPin:
    """Tests for POST /auth/check-pin."""

    def test_check_pin_not_authenticated_when_pin_not_claimed(self, client):
        """When PIN not claimed, return authenticated False."""
        with patch(
            "scruffy.frameworks_and_drivers.api.routes.auth.check_plex_pin",
            new_callable=AsyncMock,
            return_value=None,
        ):
            response = client.post("/auth/check-pin?pin_id=123")
        assert response.status_code == 200
        assert response.json()["authenticated"] is False
        assert "error" not in response.json()

    def test_check_pin_not_authenticated_when_user_not_imported(
        self, client, mock_container, plex_user
    ):
        """When user not imported in Overseerr, return authenticated False and error."""
        mock_container.overseer_gateway.user_imported_by_plex_id = AsyncMock(
            return_value=False
        )
        with patch(
            "scruffy.frameworks_and_drivers.api.routes.auth.check_plex_pin",
            new_callable=AsyncMock,
            return_value=plex_user,
        ):
            response = client.post("/auth/check-pin?pin_id=123")
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is False
        assert data.get("error") == "not_imported"

    def test_check_pin_authenticated_when_user_imported(
        self, client, mock_container, plex_user
    ):
        """When user is imported in Overseerr, return authenticated True and session."""
        with patch(
            "scruffy.frameworks_and_drivers.api.routes.auth.check_plex_pin",
            new_callable=AsyncMock,
            return_value=plex_user,
        ):
            response = client.post("/auth/check-pin?pin_id=123")
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is True
        assert data["user"]["id"] == 42
        assert data["user"]["username"] == "testuser"
        assert "session_token" in data
        mock_container.overseer_gateway.user_imported_by_plex_id.assert_called_once_with(
            42
        )

    def test_check_pin_error_when_overseerr_check_fails(
        self, client, mock_container, plex_user
    ):
        """When Overseerr user check raises, return authenticated False and error."""
        mock_container.overseer_gateway.user_imported_by_plex_id = AsyncMock(
            side_effect=Exception("Overseerr unreachable")
        )
        with patch(
            "scruffy.frameworks_and_drivers.api.routes.auth.check_plex_pin",
            new_callable=AsyncMock,
            return_value=plex_user,
        ):
            response = client.post("/auth/check-pin?pin_id=123")
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is False
        assert "verify server access" in data.get("error", "")
