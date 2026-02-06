"""Media listing routes."""

import logging
import time
from dataclasses import asdict

from fastapi import APIRouter, HTTPException

from scruffy.frameworks_and_drivers.api.auth import AuthenticatedUser
from scruffy.frameworks_and_drivers.api.dependencies import ContainerDep
from scruffy.frameworks_and_drivers.database.settings_store import get_overseerr_url

logger = logging.getLogger(__name__)

router = APIRouter(tags=["media"])

# In-memory cache for GET /api/media (short TTL to reduce load on Overseerr/Radarr/Sonarr)
_MEDIA_LIST_CACHE_TTL_SECONDS = 60
_media_list_cache: dict | None = None
_media_list_cache_expires_at: float = 0


def invalidate_media_list_cache() -> None:
    """Invalidate the media list cache. Call after mutations (e.g. delete) or in tests."""
    global _media_list_cache, _media_list_cache_expires_at
    _media_list_cache = None
    _media_list_cache_expires_at = 0


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
    global _media_list_cache, _media_list_cache_expires_at

    now = time.monotonic()
    if _media_list_cache is not None and now < _media_list_cache_expires_at:
        logger.debug("Returning cached media list")
        return _media_list_cache

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
            request_json = result.request.json()
            request_json["id"] = request_json["request_id"]  # Frontend alias
            request_json["extended"] = result.retention.extended
            media_list.append(
                {
                    "request": request_json,
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
                }
            )

        overseerr_url = get_overseerr_url()
        response = {
            "media": media_list,
            "count": len(media_list),
            "overseerr_url": overseerr_url.rstrip("/") if overseerr_url else None,
        }
        _media_list_cache = response
        _media_list_cache_expires_at = now + _MEDIA_LIST_CACHE_TTL_SECONDS

        logger.info(
            "Media list retrieved",
            extra={"count": len(media_list), "user_id": user.id},
        )

        return response

    except Exception as e:
        logger.error("Failed to fetch media list", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Failed to fetch media list")
