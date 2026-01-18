"""Shared pytest fixtures for all tests."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel

from scruffy.domain.entities.media import Media
from scruffy.domain.entities.media_request import MediaRequest
from scruffy.domain.value_objects.media_status import MediaStatus
from scruffy.domain.value_objects.media_type import MediaType
from scruffy.domain.value_objects.request_status import RequestStatus
from scruffy.domain.value_objects.retention_policy import RetentionPolicy
from scruffy.frameworks_and_drivers.database.reminder_model import ReminderModel
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


@pytest.fixture
def mock_media_repository():
    """Mock media repository."""
    return Mock(spec=MediaRepositoryInterface)


@pytest.fixture
def mock_request_repository():
    """Mock request repository."""
    return Mock(spec=RequestRepositoryInterface)


@pytest.fixture
def mock_reminder_repository():
    """Mock reminder repository."""
    mock = Mock(spec=ReminderRepositoryInterface)
    mock.has_reminder = Mock(return_value=False)
    mock.add_reminder = Mock()
    return mock


@pytest.fixture
def mock_notification_service():
    """Mock notification service."""
    return Mock(spec=NotificationServiceInterface)


@pytest.fixture
def mock_http_client():
    """Mock HTTP client."""
    return AsyncMock()


@pytest.fixture
def mock_email_client():
    """Mock email client."""
    return AsyncMock()


@pytest.fixture
def in_memory_engine():
    """Create in-memory SQLite database engine."""
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def sample_media_info_dto():
    """Sample MediaInfoDTO for testing."""
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
def sample_media_info_dto_unavailable():
    """Sample unavailable MediaInfoDTO for testing."""
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
def sample_media_info_dto_tv():
    """Sample TV MediaInfoDTO for testing."""
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
def sample_media_entity(sample_media_info_dto):
    """Sample Media entity for testing."""
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
def sample_request_dto_movie():
    """Sample movie RequestDTO for testing."""
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
def sample_request_dto_tv():
    """Sample TV RequestDTO for testing."""
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


@pytest.fixture
def sample_media_request_entity(sample_request_dto_movie):
    """Sample MediaRequest entity for testing."""
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


@pytest.fixture
def retention_policy():
    """Default retention policy for testing."""
    return RetentionPolicy(retention_days=30, reminder_days=7)


@pytest.fixture
def retention_policy_custom():
    """Custom retention policy factory."""
    def _create(retention_days: int = 30, reminder_days: int = 7):
        return RetentionPolicy(retention_days=retention_days, reminder_days=reminder_days)
    return _create
