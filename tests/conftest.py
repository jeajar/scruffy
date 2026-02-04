"""Shared pytest fixtures for all tests.

This module provides common fixtures used across the test suite.
Fixtures are organized by category for better maintainability.
"""

# CRITICAL: Disable email before any application code loads.
# Ensures tests never send real emails, even with EMAIL_ENABLED=True in .env
import os

os.environ["EMAIL_ENABLED"] = "False"

from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy import Engine, create_engine
from sqlmodel import SQLModel

from scruffy.domain.entities.media import Media
from scruffy.domain.entities.media_request import MediaRequest
from scruffy.domain.value_objects.media_status import MediaStatus
from scruffy.domain.value_objects.media_type import MediaType
from scruffy.domain.value_objects.request_status import RequestStatus
from scruffy.domain.value_objects.retention_policy import RetentionPolicy
from scruffy.use_cases.dtos.media_info_dto import MediaInfoDTO
from scruffy.use_cases.dtos.request_dto import RequestDTO
from scruffy.use_cases.interfaces.media_repository_interface import (
    MediaRepositoryInterface,
)
from scruffy.use_cases.interfaces.notification_service_interface import (
    NotificationServiceInterface,
)
from scruffy.use_cases.interfaces.reminder_repository_interface import (
    ReminderRepositoryInterface,
)
from scruffy.use_cases.interfaces.request_repository_interface import (
    RequestRepositoryInterface,
)


# =============================================================================
# Mock Repository Fixtures
# =============================================================================


@pytest.fixture
def mock_media_repository() -> Mock:
    """Create a mock media repository with spec from interface."""
    return Mock(spec=MediaRepositoryInterface)


@pytest.fixture
def mock_request_repository() -> Mock:
    """Create a mock request repository with spec from interface."""
    return Mock(spec=RequestRepositoryInterface)


@pytest.fixture
def mock_reminder_repository() -> Mock:
    """Create a mock reminder repository with pre-configured methods."""
    mock = Mock(spec=ReminderRepositoryInterface)
    mock.has_reminder = Mock(return_value=False)
    mock.add_reminder = Mock()
    return mock


@pytest.fixture
def mock_notification_service() -> Mock:
    """Create a mock notification service with spec from interface."""
    return Mock(spec=NotificationServiceInterface)


# =============================================================================
# Mock Client Fixtures
# =============================================================================


@pytest.fixture
def mock_http_client() -> AsyncMock:
    """Create an async mock HTTP client."""
    return AsyncMock()


@pytest.fixture
def mock_email_client() -> AsyncMock:
    """Create an async mock email client."""
    return AsyncMock()


# =============================================================================
# Database Fixtures
# =============================================================================


@pytest.fixture
def in_memory_engine() -> Generator[Engine, None, None]:
    """Create an in-memory SQLite database engine for testing.

    Yields:
        SQLAlchemy Engine connected to in-memory SQLite database.

    Note:
        Tables are created before yielding and dropped after the test.
    """
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


# =============================================================================
# Sample Data Fixtures - DTOs
# =============================================================================


@pytest.fixture
def sample_media_info_dto() -> MediaInfoDTO:
    """Create a sample MediaInfoDTO for an available movie."""
    return MediaInfoDTO(
        id=1,
        title="Test Movie",
        available=True,
        available_since=datetime.now(UTC) - timedelta(days=25),
        size_on_disk=1000000,
        poster="http://example.com/poster.jpg",
        seasons=[],
    )


@pytest.fixture
def sample_media_info_dto_unavailable() -> MediaInfoDTO:
    """Create a sample MediaInfoDTO for an unavailable movie."""
    return MediaInfoDTO(
        id=2,
        title="Unavailable Movie",
        available=False,
        available_since=None,
        size_on_disk=0,
        poster="",
        seasons=[],
    )


@pytest.fixture
def sample_media_info_dto_tv() -> MediaInfoDTO:
    """Create a sample MediaInfoDTO for an available TV series."""
    return MediaInfoDTO(
        id=3,
        title="Test Series",
        available=True,
        available_since=datetime.now(UTC) - timedelta(days=25),
        size_on_disk=2000000,
        poster="http://example.com/poster.jpg",
        seasons=[1, 2],
    )


@pytest.fixture
def sample_request_dto_movie() -> RequestDTO:
    """Create a sample RequestDTO for a movie request."""
    return RequestDTO(
        user_id=1,
        user_email="test@example.com",
        type="movie",
        request_id=1,
        request_status=RequestStatus.APPROVED,
        updated_at=datetime.now(UTC) - timedelta(days=30),
        media_status=MediaStatus.AVAILABLE,
        media_id=99,
        external_service_id=101,
        seasons=[],
    )


@pytest.fixture
def sample_request_dto_tv() -> RequestDTO:
    """Create a sample RequestDTO for a TV series request."""
    return RequestDTO(
        user_id=2,
        user_email="tv@example.com",
        type="tv",
        request_id=2,
        request_status=RequestStatus.APPROVED,
        updated_at=datetime.now(UTC) - timedelta(days=30),
        media_status=MediaStatus.AVAILABLE,
        media_id=100,
        external_service_id=102,
        seasons=[1, 2],
    )


# =============================================================================
# Sample Data Fixtures - Domain Entities
# =============================================================================


@pytest.fixture
def sample_media_entity(sample_media_info_dto: MediaInfoDTO) -> Media:
    """Create a sample Media entity from the sample DTO."""
    return Media(
        id=sample_media_info_dto.id,
        title=sample_media_info_dto.title,
        available=sample_media_info_dto.available,
        available_since=sample_media_info_dto.available_since,
        size_on_disk=sample_media_info_dto.size_on_disk,
        poster=sample_media_info_dto.poster,
        seasons=sample_media_info_dto.seasons,
    )


@pytest.fixture
def sample_media_request_entity(sample_request_dto_movie: RequestDTO) -> MediaRequest:
    """Create a sample MediaRequest entity from the sample DTO."""
    return MediaRequest(
        user_id=sample_request_dto_movie.user_id,
        user_email=sample_request_dto_movie.user_email,
        media_type=MediaType.MOVIE,
        request_id=sample_request_dto_movie.request_id,
        request_status=sample_request_dto_movie.request_status,
        updated_at=sample_request_dto_movie.updated_at,
        media_id=sample_request_dto_movie.media_id,
        media_status=sample_request_dto_movie.media_status,
        external_service_id=sample_request_dto_movie.external_service_id,
        seasons=sample_request_dto_movie.seasons,
    )


# =============================================================================
# Configuration Fixtures
# =============================================================================


@pytest.fixture
def retention_policy() -> RetentionPolicy:
    """Create a default retention policy for testing."""
    return RetentionPolicy(retention_days=30, reminder_days=7)


@pytest.fixture
def retention_policy_factory() -> Any:
    """Factory fixture for creating custom retention policies.

    Returns:
        A callable that creates RetentionPolicy instances with custom values.

    Example:
        def test_custom_policy(retention_policy_factory):
            policy = retention_policy_factory(retention_days=60, reminder_days=14)
            assert policy.retention_days == 60
    """

    def _create(retention_days: int = 30, reminder_days: int = 7) -> RetentionPolicy:
        return RetentionPolicy(
            retention_days=retention_days, reminder_days=reminder_days
        )

    return _create


# Backwards compatibility alias
@pytest.fixture
def retention_policy_custom(retention_policy_factory: Any) -> Any:
    """Alias for retention_policy_factory for backwards compatibility."""
    return retention_policy_factory
