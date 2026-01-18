"""Authentication module with Plex OAuth support."""

import base64
import hashlib
import hmac
import json
import logging
import time
from dataclasses import asdict, dataclass
from typing import Annotated

import httpx
from fastapi import Depends, HTTPException, Request, status

from scruffy.frameworks_and_drivers.config.settings import settings

logger = logging.getLogger(__name__)

# Plex API configuration
PLEX_API_URL = "https://plex.tv/api/v2"
PLEX_APP_NAME = "Scruffy"
PLEX_CLIENT_ID = "scruffy-media-manager"

# Session configuration
SESSION_COOKIE_NAME = "scruffy_session"
SESSION_MAX_AGE = 7 * 24 * 60 * 60  # 7 days


def _get_plex_headers(client_id: str | None = None) -> dict:
    """Get standard Plex API headers."""
    return {
        "Accept": "application/json",
        "X-Plex-Product": PLEX_APP_NAME,
        "X-Plex-Client-Identifier": client_id or PLEX_CLIENT_ID,
        "X-Plex-Version": "1.0.0",
        "X-Plex-Platform": "Web",
        "X-Plex-Device": "Browser",
    }


@dataclass
class PlexUser:
    """Authenticated Plex user."""

    id: int
    uuid: str
    username: str
    email: str
    thumb: str | None = None

    @classmethod
    def from_plex_response(cls, data: dict) -> "PlexUser":
        """Create user from Plex API response."""
        return cls(
            id=data.get("id", 0),
            uuid=data.get("uuid", ""),
            username=data.get("username", data.get("title", "")),
            email=data.get("email", ""),
            thumb=data.get("thumb"),
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "PlexUser":
        """Create from dictionary."""
        return cls(**data)


def _sign_data(data: str) -> str:
    """Sign data with HMAC-SHA256."""
    key = settings.api_secret_key.encode()
    return hmac.new(key, data.encode(), hashlib.sha256).hexdigest()


def _verify_signature(data: str, signature: str) -> bool:
    """Verify HMAC signature."""
    expected = _sign_data(data)
    return hmac.compare_digest(expected, signature)


def create_session_token(user: PlexUser) -> str:
    """Create a signed session token."""
    session_data = {
        "user": user.to_dict(),
        "exp": int(time.time()) + SESSION_MAX_AGE,
    }
    data_json = json.dumps(session_data, separators=(",", ":"))
    encoded = base64.urlsafe_b64encode(data_json.encode()).decode()
    signature = _sign_data(data_json)
    return f"{encoded}.{signature}"


def verify_session_token(token: str) -> PlexUser | None:
    """Verify and decode a session token."""
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None

        encoded, signature = parts
        data_json = base64.urlsafe_b64decode(encoded.encode()).decode()

        if not _verify_signature(data_json, signature):
            logger.warning("Invalid session signature")
            return None

        session_data = json.loads(data_json)

        if session_data.get("exp", 0) < time.time():
            logger.debug("Session expired")
            return None

        return PlexUser.from_dict(session_data["user"])

    except Exception as e:
        logger.warning("Failed to verify session", extra={"error": str(e)})
        return None


async def create_plex_pin() -> dict:
    """
    Create a Plex PIN for authentication.

    Returns dict with 'id', 'code', and 'auth_url'.
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PLEX_API_URL}/pins",
            headers=_get_plex_headers(),
            data={"strong": "true"},
            timeout=10.0,
        )
        response.raise_for_status()
        data = response.json()

        pin_id = data["id"]
        pin_code = data["code"]

        # Build the auth URL
        auth_url = (
            f"https://app.plex.tv/auth#?"
            f"clientID={PLEX_CLIENT_ID}&"
            f"code={pin_code}&"
            f"context%5Bdevice%5D%5Bproduct%5D={PLEX_APP_NAME}"
        )

        return {
            "id": pin_id,
            "code": pin_code,
            "auth_url": auth_url,
        }


async def check_plex_pin(pin_id: int) -> PlexUser | None:
    """
    Check if a Plex PIN has been claimed.

    Returns PlexUser if authenticated, None if still pending.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{PLEX_API_URL}/pins/{pin_id}",
            headers=_get_plex_headers(),
            timeout=10.0,
        )
        response.raise_for_status()
        data = response.json()

        auth_token = data.get("authToken")
        if not auth_token:
            return None

        # Get user info with the token
        user_response = await client.get(
            f"{PLEX_API_URL}/user",
            headers={
                **_get_plex_headers(),
                "X-Plex-Token": auth_token,
            },
            timeout=10.0,
        )
        user_response.raise_for_status()
        user_data = user_response.json()

        return PlexUser.from_plex_response(user_data)


async def get_current_user(request: Request) -> PlexUser:
    """
    Get the current authenticated user from session cookie.

    Raises HTTPException if not authenticated.
    """
    session_token = request.cookies.get(SESSION_COOKIE_NAME)

    if not session_token:
        logger.debug("No session cookie")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    user = verify_session_token(session_token)
    if not user:
        logger.debug("Invalid or expired session")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired",
        )

    return user


# Keep the old function name for compatibility
async def verify_overseerr_session(request: Request) -> PlexUser:
    """Verify user session (alias for get_current_user)."""
    return await get_current_user(request)


async def verify_api_key(request: Request) -> bool:
    """
    Verify API key for internal/automated requests.

    Checks for X-Api-Key header matching the configured Overseerr API key.
    This allows cron jobs and automation to call task endpoints.
    """
    api_key = request.headers.get("X-Api-Key")

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
        )

    if api_key != settings.overseerr_api_key:
        logger.warning("Invalid API key provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    logger.debug("Request authenticated via API key")
    return True


# Type aliases for dependency injection
AuthenticatedUser = Annotated[PlexUser, Depends(verify_overseerr_session)]
ApiKeyAuth = Annotated[bool, Depends(verify_api_key)]
