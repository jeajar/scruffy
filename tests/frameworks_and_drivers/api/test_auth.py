"""Tests for authentication module."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi import HTTPException

from scruffy.frameworks_and_drivers.api.auth import (
    OverseerrUser,
    verify_api_key,
    verify_overseerr_session,
)


class TestOverseerrUser:
    """Tests for OverseerrUser dataclass."""

    def test_from_overseerr_response_full(self):
        """Test creating user from full Overseerr response."""
        data = {
            "id": 1,
            "email": "test@example.com",
            "username": "testuser",
            "plexUsername": "plexuser",
            "avatar": "http://example.com/avatar.jpg",
        }

        user = OverseerrUser.from_overseerr_response(data)

        assert user.id == 1
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.plex_username == "plexuser"
        assert user.avatar == "http://example.com/avatar.jpg"

    def test_from_overseerr_response_minimal(self):
        """Test creating user from minimal Overseerr response."""
        data = {
            "id": 2,
            "email": "minimal@example.com",
            "displayName": "Display Name",
        }

        user = OverseerrUser.from_overseerr_response(data)

        assert user.id == 2
        assert user.email == "minimal@example.com"
        assert user.username == "Display Name"
        assert user.plex_username is None
        assert user.avatar is None

    def test_from_overseerr_response_empty(self):
        """Test creating user from empty response."""
        data = {}

        user = OverseerrUser.from_overseerr_response(data)

        assert user.id == 0
        assert user.email == ""
        assert user.username == ""


class TestVerifyOverseerrSession:
    """Tests for verify_overseerr_session function."""

    @pytest.fixture
    def mock_request(self):
        """Create mock request with cookies."""
        request = AsyncMock()
        request.cookies = {"connect.sid": "test-session-id"}
        return request

    @pytest.fixture
    def mock_request_no_cookies(self):
        """Create mock request without cookies."""
        request = AsyncMock()
        request.cookies = {}
        return request

    @pytest.mark.asyncio
    async def test_no_cookies_raises_401(self, mock_request_no_cookies):
        """Test that missing cookies raises 401."""
        with pytest.raises(HTTPException) as exc_info:
            await verify_overseerr_session(mock_request_no_cookies)

        assert exc_info.value.status_code == 401
        assert "no session cookie" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch("scruffy.frameworks_and_drivers.api.auth.httpx.AsyncClient")
    async def test_successful_auth(self, mock_client_class, mock_request):
        """Test successful authentication via Overseerr."""
        from unittest.mock import Mock

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 1,
            "email": "test@example.com",
            "username": "testuser",
        }

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client_class.return_value = mock_client

        with patch("scruffy.frameworks_and_drivers.api.auth.settings") as mock_settings:
            mock_settings.overseerr_url = "http://overseerr:5055"

            user = await verify_overseerr_session(mock_request)

            assert user.id == 1
            assert user.email == "test@example.com"
            assert user.username == "testuser"

    @pytest.mark.asyncio
    @patch("scruffy.frameworks_and_drivers.api.auth.httpx.AsyncClient")
    async def test_overseerr_returns_401(self, mock_client_class, mock_request):
        """Test that Overseerr 401 raises HTTPException."""
        mock_response = AsyncMock()
        mock_response.status_code = 401

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client_class.return_value = mock_client

        with patch("scruffy.frameworks_and_drivers.api.auth.settings") as mock_settings:
            mock_settings.overseerr_url = "http://overseerr:5055"

            with pytest.raises(HTTPException) as exc_info:
                await verify_overseerr_session(mock_request)

            assert exc_info.value.status_code == 401
            assert "Not authenticated with Overseerr" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch("scruffy.frameworks_and_drivers.api.auth.httpx.AsyncClient")
    async def test_overseerr_connection_error(self, mock_client_class, mock_request):
        """Test that connection error raises 502."""
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.RequestError("Connection failed")
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client_class.return_value = mock_client

        with patch("scruffy.frameworks_and_drivers.api.auth.settings") as mock_settings:
            mock_settings.overseerr_url = "http://overseerr:5055"

            with pytest.raises(HTTPException) as exc_info:
                await verify_overseerr_session(mock_request)

            assert exc_info.value.status_code == 502
            assert "Cannot connect to Overseerr" in exc_info.value.detail


class TestVerifyApiKey:
    """Tests for verify_api_key function."""

    @pytest.fixture
    def mock_request_with_key(self):
        """Create mock request with API key header."""
        request = AsyncMock()
        request.headers = {"X-Api-Key": "valid-api-key"}
        return request

    @pytest.fixture
    def mock_request_no_key(self):
        """Create mock request without API key header."""
        request = AsyncMock()
        request.headers = {}
        return request

    @pytest.mark.asyncio
    async def test_no_api_key_raises_401(self, mock_request_no_key):
        """Test that missing API key raises 401."""
        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key(mock_request_no_key)

        assert exc_info.value.status_code == 401
        assert "API key required" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_invalid_api_key_raises_401(self, mock_request_with_key):
        """Test that invalid API key raises 401."""
        with patch("scruffy.frameworks_and_drivers.api.auth.settings") as mock_settings:
            mock_settings.overseerr_api_key = "different-key"

            with pytest.raises(HTTPException) as exc_info:
                await verify_api_key(mock_request_with_key)

            assert exc_info.value.status_code == 401
            assert "Invalid API key" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_valid_api_key_succeeds(self, mock_request_with_key):
        """Test that valid API key succeeds."""
        with patch("scruffy.frameworks_and_drivers.api.auth.settings") as mock_settings:
            mock_settings.overseerr_api_key = "valid-api-key"

            result = await verify_api_key(mock_request_with_key)

            assert result is True
