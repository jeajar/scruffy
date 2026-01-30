"""Media listing routes."""

import logging
from dataclasses import asdict

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from scruffy.frameworks_and_drivers.api.auth import (
    SESSION_COOKIE_NAME,
    AuthenticatedUser,
    verify_session_token,
)
from scruffy.frameworks_and_drivers.api.dependencies import ContainerDep
from scruffy.frameworks_and_drivers.config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["media"])


@router.get("/api/media")
async def get_media_list(
    container: ContainerDep,
    user: AuthenticatedUser,
):
    """
    Get list of media requests with retention information.

    Returns JSON list of all available media with days until deletion.
    Requires authentication via Overseerr session.
    """
    logger.info(
        "Fetching media list",
        extra={"user_id": user.id, "username": user.username},
    )

    try:
        results = await container.check_media_requests_use_case.execute_with_retention(
            container.retention_calculator
        )

        # Sort by days_left ascending (soonest deletion first)
        results_sorted = sorted(results, key=lambda r: r.retention.days_left)

        # Convert to JSON-serializable format
        media_list = []
        for result in results_sorted:
            media_list.append({
                "request": result.request.json(),
                "media": {
                    "id": result.media.id,
                    "title": result.media.title,
                    "poster": result.media.poster,
                    "seasons": result.media.seasons,
                    "size_on_disk": result.media.size_on_disk,
                    "available_since": (
                        result.media.available_since.isoformat()
                        if result.media.available_since
                        else None
                    ),
                    "available": result.media.available,
                },
                "retention": asdict(result.retention),
            })

        logger.info(
            "Media list retrieved",
            extra={"count": len(media_list), "user_id": user.id},
        )

        return {"media": media_list, "count": len(media_list)}

    except Exception as e:
        logger.error("Failed to fetch media list", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Failed to fetch media list")


@router.get("/", response_class=HTMLResponse)
async def media_list_page(
    request: Request,
    container: ContainerDep,
):
    """
    Render the media list web page.

    If user is not authenticated, redirects to Plex login.
    """
    from fastapi.responses import RedirectResponse

    # Read session cookie (same as API; manual check to return redirect instead of 401)
    session_token = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_token:
        logger.debug("User not authenticated, redirecting to login")
        return RedirectResponse(url="/auth/login", status_code=302)

    user = verify_session_token(session_token)
    if not user:
        logger.debug("Invalid or expired session, redirecting to login")
        return RedirectResponse(url="/auth/login", status_code=302)

    logger.info(
        "Rendering media list page",
        extra={"user_id": user.id, "username": user.username},
    )

    try:
        results = await container.check_media_requests_use_case.execute_with_retention(
            container.retention_calculator
        )

        # Sort by days_left ascending (soonest deletion first)
        results_sorted = sorted(results, key=lambda r: r.retention.days_left)

        templates = request.app.state.templates
        return templates.TemplateResponse(
            request,
            "media_list.html",
            {
                "user": user,
                "media_list": results_sorted,
                "retention_days": settings.retention_days,
                "reminder_days": settings.reminder_days,
            },
        )

    except Exception as e:
        logger.error("Failed to render media list page", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Failed to load media list")
