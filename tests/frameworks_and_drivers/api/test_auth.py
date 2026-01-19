"""Tests for authentication module."""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi import HTTPException

from scruffy.frameworks_and_drivers.api.auth import (
    PlexUser,
    create_session_token,
    verify_api_key,
    verify_overseerr_session,
    verify_session_token,
)


class TestPlexUser:
    """Tests for PlexUser dataclass."""

    def test_from_plex_response_full(self):
        """Test creating user from full Plex response."""
        data = {
            "id": 1,
            "uuid": "abc-123",
            "email": "test@example.com",
            "username": "testuser",
            "thumb": "http://example.com/avatar.jpg",
        }

        user = PlexUser.from_plex_response(data)

        assert user.id == 1
        assert user.uuid == "abc-123"
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.thumb == "http://example.com/avatar.jpg"

    def test_from_plex_response_minimal(self):
        """Test creating user from minimal Plex response."""
        data = {
            "id": 2,
            "uuid": "def-456",
            "email": "minimal@example.com",
            "title": "Display Name",
        }

        user = PlexUser.from_plex_response(data)

        assert user.id == 2
        assert user.uuid == "def-456"
        assert user.email == "minimal@example.com"
        assert user.username == "Display Name"
        assert user.thumb is None

    def test_from_plex_response_empty(self):
        """Test creating user from empty response."""
        data = {}

        user = PlexUser.from_plex_response(data)

        assert user.id == 0
        assert user.uuid == ""
        assert user.email == ""
        assert user.username == ""

    def test_to_dict(self):
        """Test converting user to dictionary."""
        user = PlexUser(
            id=1,
            uuid="abc-123",
            username="testuser",
            email="test@example.com",
            thumb="http://example.com/avatar.jpg",
        )

        result = user.to_dict()

        assert result == {
            "id": 1,
            "uuid": "abc-123",
            "username": "testuser",
            "email": "test@example.com",
            "thumb": "http://example.com/avatar.jpg",
        }

    def test_from_dict(self):
        """Test creating user from dictionary."""
        data = {
            "id": 1,
            "uuid": "abc-123",
            "username": "testuser",
            "email": "test@example.com",
            "thumb": "http://example.com/avatar.jpg",
        }

        user = PlexUser.from_dict(data)

        assert user.id == 1
        assert user.uuid == "abc-123"
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.thumb == "http://example.com/avatar.jpg"


class TestSessionToken:
    """Tests for session token creation and verification."""

    @pytest.fixture
    def sample_user(self):
        """Create a sample PlexUser."""
        return PlexUser(
            id=1,
            uuid="abc-123",
            username="testuser",
            email="test@example.com",
            thumb=None,
        )

    @pytest.fixture
    def mock_settings(self):
        """Mock settings with a secret key."""
        with patch("scruffy.frameworks_and_drivers.api.auth.settings") as mock:
            mock.api_secret_key = "test-secret-key-for-signing"
            yield mock

    def test_create_and_verify_token(self, sample_user, mock_settings):
        """Test that created tokens can be verified."""
        token = create_session_token(sample_user)

        verified_user = verify_session_token(token)

        assert verified_user is not None
        assert verified_user.id == sample_user.id
        assert verified_user.uuid == sample_user.uuid
        assert verified_user.email == sample_user.email

    def test_verify_invalid_token_format(self, mock_settings):
        """Test that invalid token format returns None."""
        result = verify_session_token("invalid-token-no-dot")
        assert result is None

    def test_verify_tampered_token(self, sample_user, mock_settings):
        """Test that tampered tokens are rejected."""
        token = create_session_token(sample_user)
        # Tamper with the signature part of the token
        parts = token.split(".")
        tampered_signature = parts[1][:-4] + "xxxx"  # Modify signature
        tampered_token = f"{parts[0]}.{tampered_signature}"

        result = verify_session_token(tampered_token)
        assert result is None

    def test_verify_expired_token(self, sample_user, mock_settings):
        """Test that expired tokens are rejected."""
        # Create a token that's already expired
        with patch("scruffy.frameworks_and_drivers.api.auth.time.time") as mock_time:
            # Set time to past when creating
            mock_time.return_value = time.time() - 86400 * 8  # 8 days ago
            token = create_session_token(sample_user)

        # Verify with current time
        result = verify_session_token(token)
        assert result is None


class TestVerifyOverseerrSession:
    """Tests for verify_overseerr_session function."""

    @pytest.fixture
    def mock_request_with_session(self):
        """Create mock request with session cookie."""
        request = MagicMock()
        request.cookies = {"scruffy_session": "valid-token"}
        return request

    @pytest.fixture
    def mock_request_no_cookies(self):
        """Create mock request without cookies."""
        request = MagicMock()
        request.cookies = {}
        return request

    @pytest.mark.asyncio
    async def test_no_cookies_raises_401(self, mock_request_no_cookies):
        """Test that missing cookies raises 401."""
        with pytest.raises(HTTPException) as exc_info:
            await verify_overseerr_session(mock_request_no_cookies)

        assert exc_info.value.status_code == 401
        assert "Not authenticated" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_invalid_session_raises_401(self, mock_request_with_session):
        """Test that invalid session raises 401."""
        with patch(
            "scruffy.frameworks_and_drivers.api.auth.verify_session_token"
        ) as mock_verify:
            mock_verify.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                await verify_overseerr_session(mock_request_with_session)

            assert exc_info.value.status_code == 401
            assert "Session expired" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_valid_session_returns_user(self, mock_request_with_session):
        """Test that valid session returns user."""
        expected_user = PlexUser(
            id=1,
            uuid="abc-123",
            username="testuser",
            email="test@example.com",
        )

        with patch(
            "scruffy.frameworks_and_drivers.api.auth.verify_session_token"
        ) as mock_verify:
            mock_verify.return_value = expected_user

            user = await verify_overseerr_session(mock_request_with_session)

            assert user.id == expected_user.id
            assert user.email == expected_user.email


class TestVerifyApiKey:
    """Tests for verify_api_key function."""

    @pytest.fixture
    def mock_request_with_key(self):
        """Create mock request with API key header."""
        request = MagicMock()
        request.headers = {"X-Api-Key": "valid-api-key"}
        return request

    @pytest.fixture
    def mock_request_no_key(self):
        """Create mock request without API key header."""
        request = MagicMock()
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
