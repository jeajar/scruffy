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
from scruffy.use_cases.dtos.media_check_result_dto import (
    MediaCheckResultDTO,
    RetentionResultDTO,
)
from scruffy.use_cases.dtos.request_dto import RequestDTO
from scruffy.use_cases.mappers import map_media_entity_to_dto
from scruffy.use_cases.process_media_use_case import ProcessMediaUseCase
from scruffy.use_cases.send_reminder_use_case import SendReminderUseCase


def _make_check_result(
    request: MediaRequest,
    media: Media,
    *,
    remind: bool,
    delete: bool,
    days_left: int = 0,
    extended: bool = False,
    reminder_sent: bool = False,
) -> MediaCheckResultDTO:
    """Build MediaCheckResultDTO from entities for testing."""
    request_dto = RequestDTO(
        user_id=request.user_id,
        user_email=request.user_email,
        type="movie" if request.media_type == MediaType.MOVIE else "tv",
        request_id=request.request_id,
        request_status=request.request_status,
        updated_at=request.updated_at,
        media_id=request.media_id,
        media_status=request.media_status,
        external_service_id=request.external_service_id,
        seasons=request.seasons,
        tmdb_id=None,
    )
    media_dto = map_media_entity_to_dto(media)
    retention = RetentionResultDTO(
        remind=remind,
        delete=delete,
        days_left=days_left,
        extended=extended,
        reminder_sent=reminder_sent,
    )
    return MediaCheckResultDTO(
        request=request_dto, media=media_dto, retention=retention
    )


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
    """Test execute calls check use case execute_with_retention."""
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
    result = _make_check_result(
        sample_request, media_no_action, remind=False, delete=False, days_left=25
    )
    mock_check_use_case.execute_with_retention = AsyncMock(return_value=[result])

    summary = await use_case.execute()

    mock_check_use_case.execute_with_retention.assert_called_once_with(
        use_case.retention_calculator
    )
    assert summary == {
        "reminders_sent": [],
        "needs_attention": [],
        "deletions": [],
    }


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
    result = _make_check_result(
        sample_request, reminder_media, remind=True, delete=False, days_left=6
    )
    mock_check_use_case.execute_with_retention = AsyncMock(return_value=[result])
    mock_send_reminder_use_case.execute = AsyncMock()

    summary = await use_case.execute()

    mock_send_reminder_use_case.execute.assert_called_once()
    call_args = mock_send_reminder_use_case.execute.call_args
    req, med, days_left = call_args[0]
    assert req.request_id == sample_request.request_id
    assert med.title == reminder_media.title
    assert call_args[0][2] == 6  # days_left
    assert len(summary["reminders_sent"]) == 1
    assert summary["reminders_sent"][0]["email"] == "test@example.com"
    assert summary["reminders_sent"][0]["title"] == "Test Movie"
    assert summary["reminders_sent"][0]["days_left"] == 6
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
    result = _make_check_result(
        sample_request, sample_media, remind=True, delete=True, days_left=0
    )
    mock_check_use_case.execute_with_retention = AsyncMock(return_value=[result])
    mock_delete_media_use_case.execute = AsyncMock()

    summary = await use_case.execute()

    mock_delete_media_use_case.execute.assert_called_once()
    call_args = mock_delete_media_use_case.execute.call_args
    req, med = call_args[0][:2]
    assert req.request_id == sample_request.request_id
    assert med.title == sample_media.title
    assert len(summary["deletions"]) == 1
    assert summary["deletions"][0]["email"] == "test@example.com"
    assert summary["deletions"][0]["title"] == "Test Movie"
    # sample_media is 31 days old so past retention; may also trigger reminder
    assert "reminders_sent" in summary
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
    result = _make_check_result(
        sample_request, sample_media, remind=True, delete=True, days_left=0
    )
    mock_check_use_case.execute_with_retention = AsyncMock(return_value=[result])
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

    result1 = _make_check_result(
        request1, media1, remind=True, delete=True, days_left=0
    )
    result2 = _make_check_result(
        request2, media2, remind=True, delete=False, days_left=6
    )
    mock_check_use_case.execute_with_retention = AsyncMock(
        return_value=[result1, result2]
    )
    mock_send_reminder_use_case.execute = AsyncMock()
    mock_delete_media_use_case.execute = AsyncMock()

    await use_case.execute()

    # Should process both: 2 reminders (both in remind zone), 1 delete (only media1)
    assert mock_send_reminder_use_case.execute.call_count == 2
    assert mock_delete_media_use_case.execute.call_count == 1


@pytest.mark.asyncio
async def test_execute_handles_empty_results(use_case, mock_check_use_case):
    """Test execute handles empty results from check use case."""
    mock_check_use_case.execute_with_retention = AsyncMock(return_value=[])

    summary = await use_case.execute()

    # Should complete without errors
    mock_check_use_case.execute_with_retention.assert_called_once_with(
        use_case.retention_calculator
    )
    assert summary == {
        "reminders_sent": [],
        "needs_attention": [],
        "deletions": [],
    }


@pytest.mark.asyncio
async def test_execute_adds_to_needs_attention_when_reminder_already_sent(
    use_case,
    mock_check_use_case,
    mock_send_reminder_use_case,
    sample_request,
):
    """Test that when reminder was already sent, item goes to needs_attention not reminders_sent."""
    reminder_media = Media(
        id=1,
        title="Already Reminded Movie",
        available=True,
        available_since=datetime.now(UTC) - timedelta(days=24),
        size_on_disk=1000000,
        poster="",
        seasons=[],
    )
    result = _make_check_result(
        sample_request,
        reminder_media,
        remind=True,
        delete=False,
        days_left=6,
        reminder_sent=True,
    )
    mock_check_use_case.execute_with_retention = AsyncMock(return_value=[result])
    mock_send_reminder_use_case.execute = AsyncMock()

    summary = await use_case.execute()

    mock_send_reminder_use_case.execute.assert_called_once()
    assert len(summary["reminders_sent"]) == 0
    assert len(summary["needs_attention"]) == 1
    assert summary["needs_attention"][0]["title"] == "Already Reminded Movie"
    assert summary["needs_attention"][0]["days_left"] == 6
    assert summary["deletions"] == []


@pytest.mark.asyncio
async def test_execute_does_not_remind_or_delete_extended_request_in_safe_zone(
    use_case,
    mock_check_use_case,
    mock_send_reminder_use_case,
    mock_delete_media_use_case,
    sample_request,
):
    """Test that an extended request is not reminded/deleted when extension places it in safe zone.

    Without extension: media 24 days old would trigger reminder (6 days left).
    With extension (extended=True in result): execute_with_retention already applied
    extension_days, so retention shows remind=False, delete=False. No action should be taken.
    """
    # Media 24 days old - without extension would trigger remind (6 days left)
    media_24_days = Media(
        id=1,
        title="Extended Movie",
        available=True,
        available_since=datetime.now(UTC) - timedelta(days=24),
        size_on_disk=1000000,
        poster="",
        seasons=[],
    )
    # Result with extended=True and remind=False, delete=False (extension moved it to safe zone)
    result = _make_check_result(
        sample_request,
        media_24_days,
        remind=False,
        delete=False,
        days_left=13,
        extended=True,
    )
    mock_check_use_case.execute_with_retention = AsyncMock(return_value=[result])
    mock_send_reminder_use_case.execute = AsyncMock()
    mock_delete_media_use_case.execute = AsyncMock()

    summary = await use_case.execute()

    mock_send_reminder_use_case.execute.assert_not_called()
    mock_delete_media_use_case.execute.assert_not_called()
    assert summary == {
        "reminders_sent": [],
        "needs_attention": [],
        "deletions": [],
    }
