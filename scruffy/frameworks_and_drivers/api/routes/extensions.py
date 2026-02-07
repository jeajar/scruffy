"""Routes for requesting time extensions on media requests."""

import logging

from fastapi import APIRouter, HTTPException, status

from scruffy.frameworks_and_drivers.api.auth import AuthenticatedUser
from scruffy.frameworks_and_drivers.api.dependencies import ContainerDep
from scruffy.frameworks_and_drivers.api.routes.media import invalidate_media_list_cache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/requests", tags=["requests", "extensions"])


@router.post("/{request_id}/extend")
async def extend_request(
    request_id: int,
    container: ContainerDep,
    user: AuthenticatedUser,
):
    """
    Request a time extension for a media request.

    Requires authentication. Each request can only be extended once.
    Returns 200 on success, 409 if already extended, 404 if request not found.
    """
    try:
        extended = await container.request_extension_use_case.execute(
            request_id, user.id
        )
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Request not found",
            ) from e
        if "not yet available" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
            ) from e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg,
        ) from e

    if not extended:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Request has already been extended",
        )

    invalidate_media_list_cache()
    logger.info(
        "Request extended",
        extra={"request_id": request_id, "user_id": user.id},
    )
    return {"status": "extended", "request_id": request_id}
