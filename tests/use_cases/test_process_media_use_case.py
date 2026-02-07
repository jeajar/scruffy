"""Tests for ProcessMediaUseCase."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock

import pytest

from scruffy.domain.entities.media import Media
from scruffy.domain.entities.media_request import MediaRequest
from scruffy.domain.value_objects.media_status import MediaStatus
from scruffy.domain.value_objects.media_type import MediaType
from scruffy.domain.value_objects.request_status import RequestStatus
from scruffy.use_cases.check_media_requests_use_case import CheckMediaRequestsUseCase
from scruffy.use_cases.delete_media_use_case import DeleteMediaUseCase
from scruffy.use_cases.process_media_use_case import ProcessMediaUseCase
from scruffy.use_cases.send_reminder_use_case import SendReminderUseCase


@pytest.fixture
def mock_check_use_case():
    """Mock CheckMediaRequestsUseCase."""
    return Mock(spec=CheckMediaRequestsUseCase)


@pytest.fixture
def mock_send_reminder_use_case():
    """Mock SendReminderUseCase."""
    return Mock(spec=SendReminderUseCase)


@pytest.fixture
def mock_delete_media_use_case():
    """Mock DeleteMediaUseCase."""
    return Mock(spec=DeleteMediaUseCase)


@pytest.fixture
def use_case(
    mock_check_use_case,
    mock_send_reminder_use_case,
    mock_delete_media_use_case,
    retention_policy,
):
    """Create ProcessMediaUseCase instance."""
    return ProcessMediaUseCase(
        mock_check_use_case,
        mock_send_reminder_use_case,
        mock_delete_media_use_case,
        retention_policy,
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
        available_since=datetime.now(UTC) - timedelta(days=31),
        size_on_disk=1000000,
        poster="",
        seasons=[],
    )


@pytest.mark.asyncio
async def test_execute_calls_check_use_case(
    use_case,
    mock_check_use_case,
    sample_request,
    sample_media,  # noqa: ARG001
):
    """Test execute calls check use case."""
    # Use media that does not trigger remind/delete (5 days old; retention 30, reminder 7)
    media_no_action = Media(
        id=1,
        title="Test Movie",
        available=True,
        available_since=datetime.now(UTC) - timedelta(days=5),
        size_on_disk=1000000,
        poster="",
        seasons=[],
    )
    mock_check_use_case.execute = AsyncMock(
        return_value=[(sample_request, media_no_action)]
    )

    summary = await use_case.execute()

    mock_check_use_case.execute.assert_called_once()
    assert summary == {"reminders": [], "deletions": []}


@pytest.mark.asyncio
async def test_execute_calls_send_reminder_when_remind_true(
    use_case,
    mock_check_use_case,
    mock_send_reminder_use_case,
    sample_request,
    sample_media,  # noqa: ARG001
):
    """Test execute calls send_reminder_use_case when remind is True."""
    # Media that should trigger reminder (24 days old, 6 days left)
    reminder_media = Media(
        id=1,
        title="Test Movie",
        available=True,
        available_since=datetime.now(UTC) - timedelta(days=24),
        size_on_disk=1000000,
        poster="",
        seasons=[],
    )
    mock_check_use_case.execute = AsyncMock(
        return_value=[(sample_request, reminder_media)]
    )
    mock_send_reminder_use_case.execute = AsyncMock()

    summary = await use_case.execute()

    mock_send_reminder_use_case.execute.assert_called_once()
    call_args = mock_send_reminder_use_case.execute.call_args
    assert call_args[0][0] == sample_request
    assert call_args[0][1] == reminder_media
    assert isinstance(call_args[0][2], int)  # days_left
    assert len(summary["reminders"]) == 1
    assert summary["reminders"][0]["email"] == "test@example.com"
    assert summary["reminders"][0]["title"] == "Test Movie"
    assert summary["reminders"][0]["days_left"] == call_args[0][2]
    assert summary["deletions"] == []


@pytest.mark.asyncio
async def test_execute_calls_delete_media_when_delete_true(
    use_case,
    mock_check_use_case,
    mock_delete_media_use_case,
    sample_request,
    sample_media,
):
    """Test execute calls delete_media_use_case when delete is True (media 31 days old)."""
    mock_check_use_case.execute = AsyncMock(
        return_value=[(sample_request, sample_media)]
    )
    mock_delete_media_use_case.execute = AsyncMock()

    summary = await use_case.execute()

    mock_delete_media_use_case.execute.assert_called_once()
    call_args = mock_delete_media_use_case.execute.call_args
    assert call_args[0][0] == sample_request
    assert call_args[0][1] == sample_media
    assert len(summary["deletions"]) == 1
    assert summary["deletions"][0]["email"] == "test@example.com"
    assert summary["deletions"][0]["title"] == "Test Movie"
    # sample_media is 31 days old so past retention; may also trigger reminder
    assert "reminders" in summary
    assert "deletions" in summary


@pytest.mark.asyncio
async def test_execute_calls_both_remind_and_delete_when_both_true(
    use_case,
    mock_check_use_case,
    mock_send_reminder_use_case,
    mock_delete_media_use_case,
    sample_request,
    sample_media,
):
    """Test execute calls both remind and delete when both are True."""
    mock_check_use_case.execute = AsyncMock(
        return_value=[(sample_request, sample_media)]
    )
    mock_send_reminder_use_case.execute = AsyncMock()
    mock_delete_media_use_case.execute = AsyncMock()

    await use_case.execute()

    # Both should be called when delete is True (past retention)
    mock_send_reminder_use_case.execute.assert_called_once()
    mock_delete_media_use_case.execute.assert_called_once()


@pytest.mark.asyncio
async def test_execute_handles_multiple_media(
    use_case,
    mock_check_use_case,
    mock_send_reminder_use_case,
    mock_delete_media_use_case,
):
    """Test execute handles multiple media requests."""
    request1 = MediaRequest(
        user_id=1,
        user_email="test1@example.com",
        media_type=MediaType.MOVIE,
        request_id=1,
        request_status=RequestStatus.APPROVED,
        updated_at=datetime.now(UTC),
        media_id=99,
        media_status=MediaStatus.AVAILABLE,
        external_service_id=101,
        seasons=[],
    )
    media1 = Media(
        id=1,
        title="Movie 1",
        available=True,
        available_since=datetime.now(UTC) - timedelta(days=31),
        size_on_disk=1000000,
        poster="",
        seasons=[],
    )
    request2 = MediaRequest(
        user_id=2,
        user_email="test2@example.com",
        media_type=MediaType.MOVIE,
        request_id=2,
        request_status=RequestStatus.APPROVED,
        updated_at=datetime.now(UTC),
        media_id=100,
        media_status=MediaStatus.AVAILABLE,
        external_service_id=102,
        seasons=[],
    )
    media2 = Media(
        id=2,
        title="Movie 2",
        available=True,
        available_since=datetime.now(UTC) - timedelta(days=24),
        size_on_disk=2000000,
        poster="",
        seasons=[],
    )

    mock_check_use_case.execute = AsyncMock(
        return_value=[(request1, media1), (request2, media2)]
    )
    mock_send_reminder_use_case.execute = AsyncMock()
    mock_delete_media_use_case.execute = AsyncMock()

    await use_case.execute()

    # Should process both
    assert mock_send_reminder_use_case.execute.call_count == 2
    assert (
        mock_delete_media_use_case.execute.call_count == 1
    )  # Only first one should be deleted


@pytest.mark.asyncio
async def test_execute_handles_empty_results(use_case, mock_check_use_case):
    """Test execute handles empty results from check use case."""
    mock_check_use_case.execute = AsyncMock(return_value=[])

    summary = await use_case.execute()

    # Should complete without errors
    mock_check_use_case.execute.assert_called_once()
    assert summary == {"reminders": [], "deletions": []}
