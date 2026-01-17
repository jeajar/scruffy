"""Tests for DeleteMediaUseCase."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from scruffy.domain.entities.media import Media
from scruffy.domain.entities.media_request import MediaRequest
from scruffy.domain.value_objects.media_status import MediaStatus
from scruffy.domain.value_objects.media_type import MediaType
from scruffy.domain.value_objects.request_status import RequestStatus
from scruffy.use_cases.delete_media_use_case import DeleteMediaUseCase


@pytest.fixture
def use_case(mock_media_repository, mock_request_repository, mock_notification_service):
    """Create DeleteMediaUseCase instance."""
    return DeleteMediaUseCase(
        mock_media_repository,
        mock_request_repository,
        mock_notification_service,
    )


@pytest.fixture
def sample_request():
    """Sample MediaRequest for testing."""
    return MediaRequest(
        user_id=1,
        user_email="test@example.com",
        media_type=MediaType.MOVIE,
        request_id=1,
        request_status=RequestStatus.APPROVED,
        updated_at=datetime.now(UTC),
        media_id=99,
        media_status=MediaStatus.AVAILABLE,
        external_service_id=101,
        seasons=[],
    )


@pytest.fixture
def sample_media():
    """Sample Media for testing."""
    return Media(
        id=1,
        title="Test Movie",
        available=True,
        available_since=datetime.now(UTC),
        size_on_disk=1000000,
        poster="http://example.com/poster.jpg",
        seasons=[],
    )


@pytest.mark.asyncio
async def test_execute_deletes_from_media_repository(
    use_case, mock_media_repository, sample_request, sample_media
):
    """Test execute deletes from media repository."""
    mock_media_repository.delete_media = AsyncMock()
    mock_request_repository = use_case.request_repository
    mock_request_repository.delete_request = AsyncMock()
    mock_request_repository.delete_media = AsyncMock()
    mock_notification_service = use_case.notification_service
    mock_notification_service.send_deletion_notice = AsyncMock()

    await use_case.execute(sample_request, sample_media)

    mock_media_repository.delete_media.assert_called_once_with(
        sample_request.external_service_id,
        sample_request.media_type,
        sample_request.seasons,
    )


@pytest.mark.asyncio
async def test_execute_deletes_from_request_repository(
    use_case, mock_request_repository, sample_request, sample_media
):
    """Test execute deletes request and media from request repository."""
    mock_media_repository = use_case.media_repository
    mock_media_repository.delete_media = AsyncMock()
    mock_request_repository.delete_request = AsyncMock()
    mock_request_repository.delete_media = AsyncMock()
    mock_notification_service = use_case.notification_service
    mock_notification_service.send_deletion_notice = AsyncMock()

    await use_case.execute(sample_request, sample_media)

    mock_request_repository.delete_request.assert_called_once_with(sample_request.request_id)
    mock_request_repository.delete_media.assert_called_once_with(sample_request.media_id)


@pytest.mark.asyncio
async def test_execute_sends_deletion_notice(
    use_case, mock_notification_service, sample_request, sample_media
):
    """Test execute sends deletion notification."""
    mock_media_repository = use_case.media_repository
    mock_media_repository.delete_media = AsyncMock()
    mock_request_repository = use_case.request_repository
    mock_request_repository.delete_request = AsyncMock()
    mock_request_repository.delete_media = AsyncMock()
    mock_notification_service.send_deletion_notice = AsyncMock()

    await use_case.execute(sample_request, sample_media)

    mock_notification_service.send_deletion_notice.assert_called_once()
    call_args = mock_notification_service.send_deletion_notice.call_args
    assert call_args[0][0] == sample_request.user_email
    # Second arg should be MediaInfoDTO (converted from Media entity)
    assert call_args[0][1].title == sample_media.title


@pytest.mark.asyncio
async def test_execute_calls_in_correct_order(
    use_case, mock_media_repository, mock_request_repository, mock_notification_service, sample_request, sample_media
):
    """Test execute calls methods in correct order."""
    mock_media_repository.delete_media = AsyncMock()
    mock_request_repository.delete_request = AsyncMock()
    mock_request_repository.delete_media = AsyncMock()
    mock_notification_service.send_deletion_notice = AsyncMock()

    await use_case.execute(sample_request, sample_media)

    # Verify call order
    call_order = [
        mock_media_repository.delete_media.call_count > 0,
        mock_request_repository.delete_request.call_count > 0,
        mock_request_repository.delete_media.call_count > 0,
        mock_notification_service.send_deletion_notice.call_count > 0,
    ]
    assert all(call_order)


@pytest.mark.asyncio
async def test_execute_handles_tv_with_seasons(
    use_case, mock_media_repository, sample_request, sample_media
):
    """Test execute handles TV shows with seasons."""
    tv_request = MediaRequest(
        user_id=2,
        user_email="tv@example.com",
        media_type=MediaType.TV,
        request_id=2,
        request_status=RequestStatus.APPROVED,
        updated_at=datetime.now(UTC),
        media_id=100,
        media_status=MediaStatus.AVAILABLE,
        external_service_id=102,
        seasons=[1, 2],
    )
    mock_media_repository.delete_media = AsyncMock()
    mock_request_repository = use_case.request_repository
    mock_request_repository.delete_request = AsyncMock()
    mock_request_repository.delete_media = AsyncMock()
    mock_notification_service = use_case.notification_service
    mock_notification_service.send_deletion_notice = AsyncMock()

    await use_case.execute(tv_request, sample_media)

    mock_media_repository.delete_media.assert_called_once_with(
        tv_request.external_service_id,
        tv_request.media_type,
        tv_request.seasons,
    )
