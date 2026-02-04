"""FastAPI application factory for Scruffy."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from scruffy.frameworks_and_drivers.api.scheduler import (
    shutdown_scheduler,
    start_scheduler,
)
from scruffy.frameworks_and_drivers.config.settings import settings
from scruffy.frameworks_and_drivers.di.container import Container
from scruffy.frameworks_and_drivers.utils.logging import configure_logging

logger = logging.getLogger(__name__)

# Template directory path
TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates" / "web"
STATIC_DIR = Path(__file__).parent.parent.parent / "templates"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown."""
    logger.info("Starting Scruffy API server")

    # Initialize dependency injection container
    app.state.container = Container()
    logger.info("Dependency injection container initialized")

    # Start background scheduler (loads schedule jobs from DB)
    start_scheduler(app)

    yield

    # Cleanup on shutdown
    logger.info("Shutting down Scruffy API server")
    shutdown_scheduler(app)
    await app.state.container.aclose()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    # Configure logging
    configure_logging(
        level=settings.log_level,
        log_file=settings.log_file,
        loki_enabled=settings.loki_enabled,
        loki_url=str(settings.loki_url) if settings.loki_url else None,
        loki_labels=settings.loki_labels,
    )

    app = FastAPI(
        title="Scruffy API",
        description="Media retention management for Overseerr",
        version="0.3.2",
        lifespan=lifespan,
    )

    # Add CORS middleware for frontend development
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        logger.info(
            "CORS middleware configured",
            extra={"origins": settings.cors_origins},
        )

    # Setup Jinja2 templates
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
    app.state.templates = templates

    # Mount static files (for serving images like scruffy.png)
    app.mount(
        "/static",
        StaticFiles(directory=str(STATIC_DIR)),
        name="static",
    )

    # Import and include routers
    from scruffy.frameworks_and_drivers.api.routes.auth import router as auth_router
    from scruffy.frameworks_and_drivers.api.routes.extensions import (
        router as extensions_router,
    )
    from scruffy.frameworks_and_drivers.api.routes.health import router as health_router
    from scruffy.frameworks_and_drivers.api.routes.media import router as media_router
    from scruffy.frameworks_and_drivers.api.routes.schedules import (
        router as schedules_router,
    )
    from scruffy.frameworks_and_drivers.api.routes.settings import (
        router as settings_router,
    )
    from scruffy.frameworks_and_drivers.api.routes.tasks import router as tasks_router

    app.include_router(auth_router)
    app.include_router(extensions_router)
    app.include_router(health_router)
    app.include_router(media_router)
    app.include_router(schedules_router)
    app.include_router(settings_router)
    app.include_router(tasks_router, prefix="/api/tasks")

    logger.info(
        "FastAPI application configured",
        extra={
            "api_host": settings.api_host,
            "api_port": settings.api_port,
        },
    )

    return app


def main():
    """Entry point for running the API server."""
    if not settings.api_enabled:
        logger.warning("API server is disabled in settings")
        return

    app = create_app()

    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        workers=settings.api_workers,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
