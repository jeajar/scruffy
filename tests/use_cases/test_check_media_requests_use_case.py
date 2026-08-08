"""Tests for CheckMediaRequestsUseCase."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock

import pytest

from scruffy.domain.services.retention_calculator import RetentionCalculator
from scruffy.domain.value_objects.media_status import MediaStatus
from scruffy.domain.value_objects.request_status import RequestStatus
from scruffy.use_cases.check_media_requests_use_case import CheckMediaRequestsUseCase
from scruffy.use_cases.dtos.request_dto import RequestDTO


@pytest.fixture
def use_case(mock_request_repository, mock_media_repository):
    """Create CheckMediaRequestsUseCase instance."""
    return CheckMediaRequestsUseCase(mock_request_repository, mock_media_repository)


@pytest.mark.asyncio
async def test_execute_with_retention_filters_by_media_status(
    use_case,
    mock_request_repository,
    mock_media_repository,
    sample_media_info_dto,
    retention_policy,
):
    """Test execute_with_retention filters to only AVAILABLE and PARTIALLY_AVAILABLE requests."""
    available_request = RequestDTO(
        user_id=1,
        user_email="test@example.com",
        type="movie",
        request_id=1,
        request_status=RequestStatus.APPROVED,
        updated_at=datetime(2020, 1, 1, tzinfo=UTC),
        media_status=MediaStatus.AVAILABLE,
        media_id=99,
        external_service_id=101,
        seasons=[],
    )
    partially_available_request = RequestDTO(
        user_id=2,
        user_email="test2@example.com",
        type="movie",
        request_id=2,
        request_status=RequestStatus.APPROVED,
        updated_at=datetime(2020, 1, 1, tzinfo=UTC),
        media_status=MediaStatus.PARTIALLY_AVAILABLE,
        media_id=100,
        external_service_id=102,
        seasons=[],
    )
    pending_request = RequestDTO(
        user_id=3,
        user_email="test3@example.com",
        type="movie",
        request_id=3,
        request_status=RequestStatus.APPROVED,
        updated_at=datetime(2020, 1, 1, tzinfo=UTC),
        media_status=MediaStatus.PENDING,
        media_id=101,
        external_service_id=103,
        seasons=[],
    )

    mock_request_repository.get_requests = AsyncMock(
        return_value=[available_request, partially_available_request, pending_request]
    )
    mock_media_repository.get_media = AsyncMock(return_value=sample_media_info_dto)
    calculator = RetentionCalculator(retention_policy)

    results = await use_case.execute_with_retention(calculator)

    # Should only return available and partially available
    assert len(results) == 2
    assert all(
        result.request.media_status
        in [MediaStatus.AVAILABLE, MediaStatus.PARTIALLY_AVAILABLE]
        for result in results
    )


@pytest.mark.asyncio
async def test_execute_with_retention_filters_unavailable_media(
    use_case,
    mock_request_repository,
    mock_media_repository,
    sample_request_dto_movie,
    sample_media_info_dto_unavailable,
    retention_policy,
):
    """Test execute_with_retention filters out unavailable media."""
    mock_request_repository.get_requests = AsyncMock(
        return_value=[sample_request_dto_movie]
    )
    mock_media_repository.get_media = AsyncMock(
        return_value=sample_media_info_dto_unavailable
    )
    calculator = RetentionCalculator(retention_policy)

    results = await use_case.execute_with_retention(calculator)

    assert len(results) == 0


@pytest.mark.asyncio
async def test_execute_with_retention_returns_empty_list_when_no_requests(
    use_case, mock_request_repository, retention_policy
):
    """Test execute_with_retention returns empty list when no requests."""
    mock_request_repository.get_requests = AsyncMock(return_value=[])
    calculator = RetentionCalculator(retention_policy)

    results = await use_case.execute_with_retention(calculator)

    assert results == []


@pytest.mark.asyncio
async def test_execute_with_retention_returns_dtos(
    use_case,
    mock_request_repository,
    mock_media_repository,
    sample_request_dto_movie,
    sample_media_info_dto,
    retention_policy,
):
    """Test execute_with_retention returns DTOs with retention information."""
    mock_request_repository.get_requests = AsyncMock(
        return_value=[sample_request_dto_movie]
    )
    mock_media_repository.get_media = AsyncMock(return_value=sample_media_info_dto)
    calculator = RetentionCalculator(retention_policy)

    results = await use_case.execute_with_retention(calculator)

    assert len(results) == 1
    result = results[0]
    assert result.request == sample_request_dto_movie
    assert result.media == sample_media_info_dto
    assert result.retention.remind is not None
    assert result.retention.delete is not None
    assert isinstance(result.retention.days_left, int)


@pytest.mark.asyncio
async def test_execute_with_retention_reminder_sent_false_when_no_repository(
    use_case,
    mock_request_repository,
    mock_media_repository,
    sample_request_dto_movie,
    sample_media_info_dto,
    retention_policy,
):
    """Test execute_with_retention sets reminder_sent=False when reminder_repository is None."""
    mock_request_repository.get_requests = AsyncMock(
        return_value=[sample_request_dto_movie]
    )
    mock_media_repository.get_media = AsyncMock(return_value=sample_media_info_dto)
    calculator = RetentionCalculator(retention_policy)

    results = await use_case.execute_with_retention(calculator)

    assert len(results) == 1
    assert results[0].retention.reminder_sent is False


@pytest.mark.asyncio
async def test_execute_with_retention_reminder_sent_true_when_reminder_exists(
    mock_request_repository,
    mock_media_repository,
    sample_request_dto_movie,
    sample_media_info_dto,
    retention_policy,
):
    """Test execute_with_retention sets reminder_sent=True when reminder was sent."""
    mock_reminder_repository = Mock()
    mock_reminder_repository.get_request_ids_with_reminders = Mock(
        return_value={sample_request_dto_movie.request_id}
    )
    use_case = CheckMediaRequestsUseCase(
        mock_request_repository,
        mock_media_repository,
        reminder_repository=mock_reminder_repository,
    )
    mock_request_repository.get_requests = AsyncMock(
        return_value=[sample_request_dto_movie]
    )
    mock_media_repository.get_media = AsyncMock(return_value=sample_media_info_dto)
    calculator = RetentionCalculator(retention_policy)

    results = await use_case.execute_with_retention(calculator)

    assert len(results) == 1
    assert results[0].retention.reminder_sent is True
    mock_reminder_repository.get_request_ids_with_reminders.assert_called_once_with(
        [sample_request_dto_movie.request_id]
    )


@pytest.mark.asyncio
async def test_execute_with_retention_reminder_sent_false_when_no_reminder(
    mock_request_repository,
    mock_media_repository,
    sample_request_dto_movie,
    sample_media_info_dto,
    retention_policy,
):
    """Test execute_with_retention sets reminder_sent=False when no reminder was sent."""
    mock_reminder_repository = Mock()
    mock_reminder_repository.get_request_ids_with_reminders = Mock(return_value=set())
    use_case = CheckMediaRequestsUseCase(
        mock_request_repository,
        mock_media_repository,
        reminder_repository=mock_reminder_repository,
    )
    mock_request_repository.get_requests = AsyncMock(
        return_value=[sample_request_dto_movie]
    )
    mock_media_repository.get_media = AsyncMock(return_value=sample_media_info_dto)
    calculator = RetentionCalculator(retention_policy)

    results = await use_case.execute_with_retention(calculator)

    assert len(results) == 1
    assert results[0].retention.reminder_sent is False


@pytest.mark.asyncio
async def test_execute_with_retention_handles_tv_requests(
    use_case,
    mock_request_repository,
    mock_media_repository,
    sample_request_dto_tv,
    sample_media_info_dto_tv,
    retention_policy,
):
    """Test execute_with_retention handles TV requests with seasons."""
    mock_request_repository.get_requests = AsyncMock(
        return_value=[sample_request_dto_tv]
    )
    mock_media_repository.get_media = AsyncMock(return_value=sample_media_info_dto_tv)
    calculator = RetentionCalculator(retention_policy)

    results = await use_case.execute_with_retention(calculator)

    assert len(results) == 1
    result = results[0]
    assert result.request.type == "tv"
    assert result.request.seasons == [1, 2]
    assert result.media.seasons == [1, 2]
