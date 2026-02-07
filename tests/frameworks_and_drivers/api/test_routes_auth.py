"""Tests for auth routes (login, pin, callback, check-pin, close, logout, status)."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from scruffy.frameworks_and_drivers.api.app import create_app
from scruffy.frameworks_and_drivers.api.auth import PlexUser, create_session_token


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
def mock_container(plex_user):  # noqa: ARG001
    """Mock container with overseer_gateway.user_imported_by_plex_id and get_user_by_plex_id."""
    container = Mock()
    container.overseer_gateway = Mock()
    container.overseer_gateway.user_imported_by_plex_id = AsyncMock(return_value=True)
    container.overseer_gateway.get_user_by_plex_id = AsyncMock(
        return_value={"plexId": 42, "permissions": 2}
    )
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

    def test_callback_502_when_plex_pin_check_fails(self, client):
        """When check_plex_pin raises, return 502."""
        with patch(
            "scruffy.frameworks_and_drivers.api.routes.auth.check_plex_pin",
            new_callable=AsyncMock,
            side_effect=Exception("Plex unreachable"),
        ):
            response = client.get("/auth/callback?pin_id=123")
        assert response.status_code == 502
        assert "Failed to verify with Plex" in response.json().get("detail", "")


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

    def test_check_pin_error_when_plex_pin_check_fails(self, client):
        """When check_plex_pin raises, return authenticated False and error."""
        with patch(
            "scruffy.frameworks_and_drivers.api.routes.auth.check_plex_pin",
            new_callable=AsyncMock,
            side_effect=Exception("Plex unreachable"),
        ):
            response = client.post("/auth/check-pin?pin_id=123")
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is False
        assert "Failed to verify with Plex" in data.get("error", "")


class TestLoginPage:
    """Tests for GET /auth/login."""

    def test_login_page_returns_html_with_pin_data(self, client):
        """When create_plex_pin succeeds, return HTML with pin_id and auth_url."""
        pin_data = {
            "id": 999,
            "code": "ABCD",
            "auth_url": "https://app.plex.tv/auth#?code=ABCD",
        }
        with patch(
            "scruffy.frameworks_and_drivers.api.routes.auth.create_plex_pin",
            new_callable=AsyncMock,
            return_value=pin_data,
        ):
            response = client.get("/auth/login")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
        assert b"999" in response.content  # PIN_ID in template
        assert b"app.plex.tv/auth" in response.content  # auth_url in template

    def test_login_page_502_when_plex_unreachable(self, client):
        """When create_plex_pin raises, return 502."""
        with patch(
            "scruffy.frameworks_and_drivers.api.routes.auth.create_plex_pin",
            new_callable=AsyncMock,
            side_effect=Exception("Plex unreachable"),
        ):
            response = client.get("/auth/login")
        assert response.status_code == 502
        assert "Failed to connect to Plex" in response.json().get("detail", "")


class TestCreatePin:
    """Tests for POST /auth/pin."""

    def test_create_pin_returns_json_with_pin_data(self, client):
        """When create_plex_pin succeeds, return JSON with pin_id, code, auth_url."""
        pin_data = {
            "id": 888,
            "code": "WXYZ",
            "auth_url": "https://app.plex.tv/auth#?...",
        }
        with patch(
            "scruffy.frameworks_and_drivers.api.routes.auth.create_plex_pin",
            new_callable=AsyncMock,
            return_value=pin_data,
        ):
            response = client.post("/auth/pin")
        assert response.status_code == 200
        data = response.json()
        assert data["pin_id"] == 888
        assert data["code"] == "WXYZ"
        assert data["auth_url"] == "https://app.plex.tv/auth#?..."

    def test_create_pin_502_when_plex_unreachable(self, client):
        """When create_plex_pin raises, return 502."""
        with patch(
            "scruffy.frameworks_and_drivers.api.routes.auth.create_plex_pin",
            new_callable=AsyncMock,
            side_effect=Exception("Plex unreachable"),
        ):
            response = client.post("/auth/pin")
        assert response.status_code == 502
        assert "Failed to connect to Plex" in response.json().get("detail", "")


class TestAuthClose:
    """Tests for GET /auth/close."""

    def test_auth_close_returns_html(self, client):
        """Close page returns HTML (for popup auto-close)."""
        response = client.get("/auth/close")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")


class TestLogout:
    """Tests for GET /auth/logout and POST /auth/logout."""

    def test_logout_get_redirects_and_deletes_cookie(self, client):
        """GET /auth/logout redirects to / and deletes session cookie."""
        response = client.get("/auth/logout", follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["location"] == "/"
        set_cookie = response.headers.get("set-cookie", "")
        assert "scruffy_session" in set_cookie
        assert "max-age=0" in set_cookie or "Max-Age=0" in set_cookie

    def test_logout_post_returns_json_and_deletes_cookie(self, client):
        """POST /auth/logout returns JSON success and deletes session cookie."""
        response = client.post("/auth/logout")
        assert response.status_code == 200
        assert response.json() == {"success": True}
        set_cookie = response.headers.get("set-cookie", "")
        assert "scruffy_session" in set_cookie
        assert "max-age=0" in set_cookie or "Max-Age=0" in set_cookie


class TestAuthStatus:
    """Tests for GET /auth/status."""

    def test_status_not_authenticated_when_no_cookie(self, client):
        """When no session cookie, return authenticated False."""
        response = client.get("/auth/status")
        assert response.status_code == 200
        assert response.json() == {"authenticated": False}

    def test_status_not_authenticated_when_invalid_token(self, client):
        """When session token is invalid, return authenticated False."""
        response = client.get(
            "/auth/status",
            cookies={"scruffy_session": "invalid.token.here"},
        )
        assert response.status_code == 200
        assert response.json() == {"authenticated": False}

    def test_status_authenticated_with_admin(self, client, mock_container, plex_user):
        """When valid session and user is Overseerr admin, return isAdmin True."""
        session_token = create_session_token(plex_user)
        mock_container.overseer_gateway.get_user_by_plex_id = AsyncMock(
            return_value={"plexId": 42, "permissions": 2}
        )
        response = client.get(
            "/auth/status",
            cookies={"scruffy_session": session_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is True
        assert data["isAdmin"] is True
        assert data["user"]["id"] == 42
        assert data["user"]["username"] == "testuser"

    def test_status_authenticated_with_non_admin(
        self, client, mock_container, plex_user
    ):
        """When valid session and user is not Overseerr admin, return isAdmin False."""
        session_token = create_session_token(plex_user)
        mock_container.overseer_gateway.get_user_by_plex_id = AsyncMock(
            return_value={"plexId": 42, "permissions": 0}
        )
        response = client.get(
            "/auth/status",
            cookies={"scruffy_session": session_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is True
        assert data["isAdmin"] is False
        assert data["user"]["username"] == "testuser"

    def test_status_authenticated_when_overseerr_user_not_found(
        self, client, mock_container, plex_user
    ):
        """When valid session but Overseerr returns None, isAdmin is False."""
        session_token = create_session_token(plex_user)
        mock_container.overseer_gateway.get_user_by_plex_id = AsyncMock(
            return_value=None
        )
        response = client.get(
            "/auth/status",
            cookies={"scruffy_session": session_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is True
        assert data["isAdmin"] is False
