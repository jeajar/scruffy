"""Tests for CheckMediaRequestsUseCase."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from scruffy.domain.entities.media import Media
from scruffy.domain.entities.media_request import MediaRequest
from scruffy.domain.services.retention_calculator import RetentionCalculator
from scruffy.domain.value_objects.media_status import MediaStatus
from scruffy.domain.value_objects.media_type import MediaType
from scruffy.domain.value_objects.request_status import RequestStatus
from scruffy.use_cases.check_media_requests_use_case import CheckMediaRequestsUseCase
from scruffy.use_cases.dtos.request_dto import RequestDTO


@pytest.fixture
def use_case(mock_request_repository, mock_media_repository):
    """Create CheckMediaRequestsUseCase instance."""
    return CheckMediaRequestsUseCase(mock_request_repository, mock_media_repository)


@pytest.mark.asyncio
async def test_execute_returns_available_media(
    use_case, mock_request_repository, mock_media_repository, sample_request_dto_movie, sample_media_info_dto
):
    """Test execute returns available media requests."""
    mock_request_repository.get_requests = AsyncMock(return_value=[sample_request_dto_movie])
    mock_media_repository.get_media = AsyncMock(return_value=sample_media_info_dto)

    results = await use_case.execute()

    assert len(results) == 1
    assert isinstance(results[0], tuple)
    assert isinstance(results[0][0], MediaRequest)
    assert isinstance(results[0][1], Media)
    assert results[0][0].request_id == sample_request_dto_movie.request_id
    assert results[0][1].id == sample_media_info_dto.id


@pytest.mark.asyncio
async def test_execute_filters_by_media_status(
    use_case, mock_request_repository, mock_media_repository, sample_media_info_dto
):
    """Test execute filters to only AVAILABLE and PARTIALLY_AVAILABLE requests."""
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

    results = await use_case.execute()

    # Should only return available and partially available
    assert len(results) == 2
    assert all(req.media_status in [MediaStatus.AVAILABLE, MediaStatus.PARTIALLY_AVAILABLE] for req, _ in results)


@pytest.mark.asyncio
async def test_execute_filters_unavailable_media(
    use_case, mock_request_repository, mock_media_repository, sample_request_dto_movie, sample_media_info_dto_unavailable
):
    """Test execute filters out unavailable media."""
    mock_request_repository.get_requests = AsyncMock(return_value=[sample_request_dto_movie])
    mock_media_repository.get_media = AsyncMock(return_value=sample_media_info_dto_unavailable)

    results = await use_case.execute()

    assert len(results) == 0


@pytest.mark.asyncio
async def test_execute_returns_empty_list_when_no_requests(
    use_case, mock_request_repository
):
    """Test execute returns empty list when no requests."""
    mock_request_repository.get_requests = AsyncMock(return_value=[])

    results = await use_case.execute()

    assert results == []


@pytest.mark.asyncio
async def test_execute_with_retention_returns_dtos(
    use_case, mock_request_repository, mock_media_repository, sample_request_dto_movie, sample_media_info_dto, retention_policy
):
    """Test execute_with_retention returns DTOs with retention information."""
    mock_request_repository.get_requests = AsyncMock(return_value=[sample_request_dto_movie])
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
async def test_execute_handles_tv_requests(
    use_case, mock_request_repository, mock_media_repository, sample_request_dto_tv, sample_media_info_dto_tv
):
    """Test execute handles TV requests with seasons."""
    mock_request_repository.get_requests = AsyncMock(return_value=[sample_request_dto_tv])
    mock_media_repository.get_media = AsyncMock(return_value=sample_media_info_dto_tv)

    results = await use_case.execute()

    assert len(results) == 1
    request, media = results[0]
    assert request.media_type == MediaType.TV
    assert request.seasons == [1, 2]
    assert media.seasons == [1, 2]
