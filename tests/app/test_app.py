from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock

import pytest

from scruffy.app.app import MediaManager, RetentionResult
from scruffy.infra.constants import MediaStatus, RequestStatus
from scruffy.infra.data_transfer_objects import MediaInfoDTO, RequestDTO


@pytest.fixture
def mock_overseer():
    return AsyncMock(get_requests=AsyncMock(), delete_request=AsyncMock())


@pytest.fixture
def mock_sonarr():
    return AsyncMock(get_series_info=AsyncMock(), delete_series_seasons=AsyncMock())


@pytest.fixture
def mock_radarr():
    return AsyncMock(get_movie=AsyncMock(), delete_movie=AsyncMock())


@pytest.fixture
def mock_email():
    return AsyncMock(send_reminder_notice=AsyncMock(), send_deletion_notice=AsyncMock())


@pytest.fixture
def mock_reminder_repository():
    mock = Mock()
    mock.has_reminder = Mock(return_value=False)
    mock.add_reminder = Mock()
    return mock


@pytest.fixture
def manager(
    mock_overseer, mock_sonarr, mock_radarr, mock_email, mock_reminder_repository
):
    return MediaManager(
        overseer=mock_overseer,
        sonarr=mock_sonarr,
        radarr=mock_radarr,
        email_service=mock_email,
        reminder_repository=mock_reminder_repository,
    )


@pytest.fixture
def sample_movie_request():
    return RequestDTO(
        user_id=1,
        user_email="test@example.com",
        type="movie",
        request_id=1,
        request_status=RequestStatus.APPROVED,
        updated_at=datetime.now(timezone.utc) - timedelta(days=31),
        media_status=MediaStatus.AVAILABLE,
        external_service_id=101,
        seasons=[],
    )


@pytest.fixture
def sample_movie_remind_request():
    return RequestDTO(
        user_id=2,
        user_email="test@example.com",
        type="movie",
        request_id=1,
        request_status=RequestStatus.APPROVED,
        updated_at=datetime.now(timezone.utc) - timedelta(days=23),
        media_status=MediaStatus.AVAILABLE,
        external_service_id=102,
        seasons=[],
    )


@pytest.fixture
def sample_tv_request():
    return RequestDTO(
        user_id=1,
        user_email="test@example.com",
        type="tv",
        request_id=2,
        request_status=RequestStatus.APPROVED,
        updated_at=datetime.now(timezone.utc) - timedelta(days=31),
        media_status=MediaStatus.AVAILABLE,
        external_service_id=102,
        seasons=[1],
    )


@pytest.fixture
def sample_media_info():
    return MediaInfoDTO(
        available=True,
        available_since=datetime.now(timezone.utc) - timedelta(days=31),
        id=1,
        poster="test.jpg",
        seasons=[1],
        size_on_disk=1000,
        title="Test Media",
    )


@pytest.fixture
def sample_media_remind_info():
    return MediaInfoDTO(
        available=True,
        available_since=datetime.now(timezone.utc) - timedelta(days=23),
        id=2,
        poster="test.jpg",
        seasons=[1],
        size_on_disk=1000,
        title="Test Media",
    )


@pytest.mark.asyncio
async def test_check_requests_movie(
    manager, mock_overseer, sample_movie_request, sample_media_info
):
    mock_overseer.get_requests.return_value = [sample_movie_request]
    manager.radarr.get_movie.return_value = sample_media_info

    results = await manager.check_requests()
    assert len(results) == 1
    assert results[0] == (sample_movie_request, sample_media_info)


@pytest.mark.asyncio
async def test_check_requests_tv(
    manager, mock_overseer, sample_tv_request, sample_media_info
):
    mock_overseer.get_requests.return_value = [sample_tv_request]
    manager.sonarr.get_series_info.return_value = sample_media_info

    results = await manager.check_requests()
    assert len(results) == 1
    assert results[0] == (sample_tv_request, sample_media_info)


def test_check_retention_policy(manager, sample_movie_request, sample_media_info):
    result = manager._check_retention_policy(sample_movie_request, sample_media_info)
    assert isinstance(result, RetentionResult)
    assert result.delete is True
    assert result.remind is True
    assert result.days_left < 0


@pytest.mark.asyncio
async def test_process_media_delete(
    manager,
    mock_overseer,
    mock_radarr,
    mock_email,
    sample_movie_request,
    sample_media_info,
):
    mock_overseer.get_requests.return_value = [sample_movie_request]
    manager.radarr.get_movie.return_value = sample_media_info

    await manager.process_media()

    mock_radarr.delete_movie.assert_called_once_with(
        sample_movie_request.external_service_id
    )
    mock_overseer.delete_request.assert_called_once_with(
        sample_movie_request.request_id
    )
    mock_email.send_deletion_notice.assert_called_once()


@pytest.mark.asyncio
async def test_process_media_remind(
    manager,
    mock_overseer,
    mock_email,
    sample_movie_remind_request,
    sample_media_remind_info,
):
    mock_overseer.get_requests.return_value = [sample_movie_remind_request]
    manager.radarr.get_movie.return_value = sample_media_remind_info

    await manager.process_media()

    mock_email.send_reminder_notice.assert_called_once()
    mock_overseer.delete_request.assert_not_called()


@pytest.mark.asyncio
async def test_delete_media_movie(manager, mock_radarr, sample_movie_request):
    await manager._delete_media(sample_movie_request)
    mock_radarr.delete_movie.assert_called_once_with(
        sample_movie_request.external_service_id
    )


@pytest.mark.asyncio
async def test_delete_media_tv(manager, mock_sonarr, sample_tv_request):
    await manager._delete_media(sample_tv_request)
    mock_sonarr.delete_series_seasons.assert_called_once_with(
        sample_tv_request.external_service_id, sample_tv_request.seasons
    )
