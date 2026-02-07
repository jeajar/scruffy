"""Tests for RequestExtensionUseCase."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from scruffy.domain.value_objects.media_status import MediaStatus
from scruffy.domain.value_objects.request_status import RequestStatus
from scruffy.use_cases.dtos.request_dto import RequestDTO
from scruffy.use_cases.request_extension_use_case import RequestExtensionUseCase


@pytest.fixture
def use_case(mock_extension_repository, mock_request_repository):
    """Create RequestExtensionUseCase instance."""
    return RequestExtensionUseCase(
        mock_extension_repository,
        mock_request_repository,
    )


@pytest.fixture
def sample_request_dto():
    """Sample RequestDTO for available media."""
    return RequestDTO(
        user_id=1,
        user_email="test@example.com",
        type="movie",
        request_id=1,
        request_status=RequestStatus.APPROVED,
        updated_at=datetime.now(UTC),
        media_status=MediaStatus.AVAILABLE,
        media_id=99,
        external_service_id=101,
        seasons=[],
    )


@pytest.mark.asyncio
async def test_execute_records_extension(
    use_case, mock_extension_repository, mock_request_repository, sample_request_dto
):
    """Test execute records extension when request exists and is available."""
    mock_request_repository.get_request = AsyncMock(return_value=sample_request_dto)
    mock_extension_repository.extend_request = lambda rid, pid: True

    result = await use_case.execute(1, plex_user_id=100)

    assert result is True
    mock_request_repository.get_request.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_execute_returns_false_when_already_extended(
    use_case, mock_extension_repository, mock_request_repository, sample_request_dto
):
    """Test execute returns False when request already extended."""
    mock_request_repository.get_request = AsyncMock(return_value=sample_request_dto)
    mock_extension_repository.extend_request = lambda rid, pid: False

    result = await use_case.execute(1, plex_user_id=100)

    assert result is False


@pytest.mark.asyncio
async def test_execute_raises_when_request_not_found(
    use_case,
    mock_extension_repository,  # noqa: ARG001
    mock_request_repository,  # noqa: ARG001
):
    """Test execute raises ValueError when request does not exist."""
    mock_request_repository.get_request = AsyncMock(return_value=None)

    with pytest.raises(ValueError, match="not found"):
        await use_case.execute(1, plex_user_id=100)


@pytest.mark.asyncio
async def test_execute_raises_when_media_not_available(
    use_case,
    mock_extension_repository,  # noqa: ARG001
    mock_request_repository,  # noqa: ARG001
):
    """Test execute raises ValueError when media is not yet available."""
    pending_request = RequestDTO(
        user_id=1,
        user_email="test@example.com",
        type="movie",
        request_id=1,
        request_status=RequestStatus.APPROVED,
        updated_at=datetime.now(UTC),
        media_status=MediaStatus.PENDING,
        media_id=99,
        external_service_id=101,
        seasons=[],
    )
    mock_request_repository.get_request = AsyncMock(return_value=pending_request)

    with pytest.raises(ValueError, match="not yet available"):
        await use_case.execute(1, plex_user_id=100)
