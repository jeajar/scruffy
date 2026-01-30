"""Health check routes."""

import logging

from fastapi import APIRouter

from scruffy.frameworks_and_drivers.api.dependencies import ContainerDep

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(container: ContainerDep):
    """
    Health check endpoint.

    Returns the health status of the application and its dependencies
    (Overseerr, Radarr, Sonarr). This endpoint does not require authentication.
    """
    logger.debug("Health check requested")

    overseerr_healthy = await container.overseer_gateway.status()
    radarr_healthy = await container.radarr_gateway.status()
    sonarr_healthy = await container.sonarr_gateway.status()

    all_healthy = overseerr_healthy and radarr_healthy and sonarr_healthy
    status = "healthy" if all_healthy else "degraded"

    return {
        "status": status,
        "services": {
            "overseerr": "healthy" if overseerr_healthy else "unhealthy",
            "radarr": "healthy" if radarr_healthy else "unhealthy",
            "sonarr": "healthy" if sonarr_healthy else "unhealthy",
        },
    }
