"""Authentication routes for Plex OAuth."""

import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from scruffy.frameworks_and_drivers.api.auth import (
    SESSION_COOKIE_NAME,
    SESSION_MAX_AGE,
    check_plex_pin,
    create_plex_pin,
    create_session_token,
    verify_session_token,
)
from scruffy.frameworks_and_drivers.api.dependencies import ContainerDep

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """
    Show the Plex login page.

    Creates a Plex PIN and shows a page with the auth link.
    """
    try:
        pin_data = await create_plex_pin()
    except Exception as e:
        logger.error("Failed to create Plex PIN", extra={"error": str(e)})
        raise HTTPException(status_code=502, detail="Failed to connect to Plex")

    templates = request.app.state.templates
    return templates.TemplateResponse(
        request,
        "plex_login.html",
        {
            "pin_id": pin_data["id"],
            "pin_code": pin_data["code"],
            "auth_url": pin_data["auth_url"],
        },
    )


@router.post("/pin")
async def create_pin():
    """
    Create a new Plex PIN for authentication (JSON API).

    Returns JSON with pin_id, code, and auth_url for the React frontend.
    """
    try:
        pin_data = await create_plex_pin()
    except Exception as e:
        logger.error("Failed to create Plex PIN", extra={"error": str(e)})
        raise HTTPException(status_code=502, detail="Failed to connect to Plex")

    return {
        "pin_id": pin_data["id"],
        "code": pin_data["code"],
        "auth_url": pin_data["auth_url"],
    }


@router.get("/callback")
async def auth_callback(pin_id: int, container: ContainerDep):
    """
    Handle the auth callback after Plex authentication.

    Checks if the PIN has been claimed, then verifies the user is imported
    in Overseerr (has access to our Plex server) before creating a session.
    """
    try:
        user = await check_plex_pin(pin_id)
    except Exception as e:
        logger.error("Failed to check Plex PIN", extra={"error": str(e)})
        raise HTTPException(status_code=502, detail="Failed to verify with Plex")

    if not user:
        # PIN not yet claimed - redirect back to login
        logger.debug("PIN not yet claimed", extra={"pin_id": pin_id})
        return RedirectResponse(url="/auth/login?error=not_claimed", status_code=302)

    # Ensure user is imported in Overseerr (has access to our Plex server)
    try:
        imported = await container.overseer_gateway.user_imported_by_plex_id(user.id)
    except Exception as e:
        logger.error(
            "Failed to check Overseerr for user",
            extra={"error": str(e), "user_id": user.id},
        )
        raise HTTPException(
            status_code=502,
            detail="Failed to verify server access",
        )
    if not imported:
        logger.warning(
            "Plex user not imported in Overseerr - denying login",
            extra={"user_id": user.id, "username": user.username},
        )
        return RedirectResponse(
            url="/auth/login?error=not_imported",
            status_code=302,
        )

    # Create session and redirect to home
    session_token = create_session_token(user)

    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_token,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=True,  # Set to False for local development without HTTPS
    )

    logger.info(
        "User authenticated via Plex",
        extra={"user_id": user.id, "username": user.username},
    )

    return response


@router.post("/check-pin")
async def check_pin(pin_id: int, container: ContainerDep):
    """
    API endpoint to check if a PIN has been claimed.

    Used by the login page to poll for authentication status.
    Only authorizes if the Plex user is imported in Overseerr (server access).
    """
    try:
        user = await check_plex_pin(pin_id)
    except Exception as e:
        logger.error("Failed to check Plex PIN", extra={"error": str(e)})
        return {"authenticated": False, "error": "Failed to verify with Plex"}

    if not user:
        return {"authenticated": False}

    # Ensure user is imported in Overseerr (has access to our Plex server)
    try:
        imported = await container.overseer_gateway.user_imported_by_plex_id(user.id)
    except Exception as e:
        logger.error(
            "Failed to check Overseerr for user",
            extra={"error": str(e), "user_id": user.id},
        )
        return {"authenticated": False, "error": "Failed to verify server access"}
    if not imported:
        logger.warning(
            "Plex user not imported in Overseerr - denying login",
            extra={"user_id": user.id, "username": user.username},
        )
        return {"authenticated": False, "error": "not_imported"}

    # Create session token
    session_token = create_session_token(user)

    return {
        "authenticated": True,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "thumb": user.thumb,
        },
        "session_token": session_token,
        "cookie_name": SESSION_COOKIE_NAME,
        "max_age": SESSION_MAX_AGE,
    }


@router.get("/logout")
async def logout():
    """Log out and clear the session (HTML redirect)."""
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie(SESSION_COOKIE_NAME)
    logger.info("User logged out")
    return response


@router.post("/logout")
async def logout_api():
    """Log out and clear the session (JSON API)."""
    from fastapi.responses import JSONResponse

    response = JSONResponse(content={"success": True})
    response.delete_cookie(SESSION_COOKIE_NAME)
    logger.info("User logged out via API")
    return response


@router.get("/status")
async def auth_status(request: Request):
    """Check current authentication status."""
    session_token = request.cookies.get(SESSION_COOKIE_NAME)

    if not session_token:
        return {"authenticated": False}

    user = verify_session_token(session_token)
    if not user:
        return {"authenticated": False}

    return {
        "authenticated": True,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "thumb": user.thumb,
        },
    }
