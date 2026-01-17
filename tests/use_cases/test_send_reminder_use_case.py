"""Tests for SendReminderUseCase."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from scruffy.domain.entities.media import Media
from scruffy.domain.entities.media_request import MediaRequest
from scruffy.domain.value_objects.media_status import MediaStatus
from scruffy.domain.value_objects.media_type import MediaType
from scruffy.domain.value_objects.request_status import RequestStatus
from scruffy.use_cases.send_reminder_use_case import SendReminderUseCase


@pytest.fixture
def use_case(mock_reminder_repository, mock_notification_service):
    """Create SendReminderUseCase instance."""
    return SendReminderUseCase(mock_reminder_repository, mock_notification_service)


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
async def test_execute_sends_reminder_when_no_reminder_exists(
    use_case, mock_reminder_repository, mock_notification_service, sample_request, sample_media
):
    """Test execute sends reminder when no reminder exists."""
    mock_reminder_repository.has_reminder.return_value = False
    mock_notification_service.send_reminder_notice = AsyncMock()

    await use_case.execute(sample_request, sample_media, days_left=7)

    mock_reminder_repository.has_reminder.assert_called_once_with(sample_request.request_id)
    mock_notification_service.send_reminder_notice.assert_called_once()
    call_args = mock_notification_service.send_reminder_notice.call_args
    assert call_args[0][0] == sample_request.user_email
    assert call_args[0][2] == 7  # days_left
    # Second arg should be MediaInfoDTO (converted from Media entity)
    assert call_args[0][1].title == sample_media.title


@pytest.mark.asyncio
async def test_execute_adds_reminder_after_sending(
    use_case, mock_reminder_repository, mock_notification_service, sample_request, sample_media
):
    """Test execute adds reminder record after sending notification."""
    mock_reminder_repository.has_reminder.return_value = False
    mock_notification_service.send_reminder_notice = AsyncMock()

    await use_case.execute(sample_request, sample_media, days_left=7)

    mock_reminder_repository.add_reminder.assert_called_once_with(
        sample_request.request_id,
        sample_request.user_id,
    )


@pytest.mark.asyncio
async def test_execute_skips_when_reminder_already_exists(
    use_case, mock_reminder_repository, mock_notification_service, sample_request, sample_media
):
    """Test execute skips sending when reminder already exists."""
    mock_reminder_repository.has_reminder.return_value = True
    mock_notification_service.send_reminder_notice = AsyncMock()

    await use_case.execute(sample_request, sample_media, days_left=7)

    mock_reminder_repository.has_reminder.assert_called_once_with(sample_request.request_id)
    mock_notification_service.send_reminder_notice.assert_not_called()
    mock_reminder_repository.add_reminder.assert_not_called()


@pytest.mark.asyncio
async def test_execute_with_different_days_left(
    use_case, mock_reminder_repository, mock_notification_service, sample_request, sample_media
):
    """Test execute works with different days_left values."""
    mock_reminder_repository.has_reminder.return_value = False
    mock_notification_service.send_reminder_notice = AsyncMock()

    await use_case.execute(sample_request, sample_media, days_left=3)

    call_args = mock_notification_service.send_reminder_notice.call_args
    assert call_args[0][2] == 3  # days_left
