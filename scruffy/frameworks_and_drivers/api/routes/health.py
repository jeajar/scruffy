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

    Returns the health status of the application and its dependencies.
    This endpoint does not require authentication.
    """
    logger.debug("Health check requested")

    # Check Overseerr connection
    overseerr_healthy = await container.overseer_gateway.status()

    status = "healthy" if overseerr_healthy else "degraded"

    return {
        "status": status,
        "services": {
            "overseerr": "healthy" if overseerr_healthy else "unhealthy",
        },
    }


@router.get("/health/live")
async def liveness_check():
    """
    Kubernetes liveness probe endpoint.

    Returns 200 if the application is running.
    This endpoint does not require authentication.
    """
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness_check(container: ContainerDep):
    """
    Kubernetes readiness probe endpoint.

    Returns 200 if the application is ready to serve traffic.
    Checks that all required services are available.
    This endpoint does not require authentication.
    """
    overseerr_healthy = await container.overseer_gateway.status()

    if not overseerr_healthy:
        return {"status": "not_ready", "reason": "Overseerr unavailable"}

    return {"status": "ready"}
