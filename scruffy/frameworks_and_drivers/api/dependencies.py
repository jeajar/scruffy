"""Dependency injection for FastAPI routes."""

from typing import Annotated

from fastapi import Depends, Request

from scruffy.frameworks_and_drivers.di.container import Container


def get_container(request: Request) -> Container:
    """Get the dependency injection container from app state."""
    return request.app.state.container


# Type alias for dependency injection
ContainerDep = Annotated[Container, Depends(get_container)]
