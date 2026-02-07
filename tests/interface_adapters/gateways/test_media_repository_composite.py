"""Tests for MediaRepositoryComposite."""

from unittest.mock import AsyncMock, Mock

import pytest

from scruffy.domain.value_objects.media_type import MediaType
from scruffy.interface_adapters.gateways.media_repository_composite import (
    MediaRepositoryComposite,
)
from scruffy.interface_adapters.gateways.radarr_gateway import RadarrGateway
from scruffy.interface_adapters.gateways.sonarr_gateway import SonarrGateway


@pytest.fixture
def mock_radarr_gateway():
    """Mock RadarrGateway."""
    return Mock(spec=RadarrGateway)


@pytest.fixture
def mock_sonarr_gateway():
    """Mock SonarrGateway."""
    return Mock(spec=SonarrGateway)


@pytest.fixture
def composite(mock_radarr_gateway, mock_sonarr_gateway):
    """Create MediaRepositoryComposite instance."""
    return MediaRepositoryComposite(mock_radarr_gateway, mock_sonarr_gateway)


@pytest.mark.asyncio
async def test_get_media_delegates_to_radarr_for_movie(composite, mock_radarr_gateway, sample_media_info_dto):
    """Test get_media delegates to RadarrGateway for movies."""
    mock_radarr_gateway.get_media = AsyncMock(return_value=sample_media_info_dto)

    result = await composite.get_media(1, MediaType.MOVIE, [])

    mock_radarr_gateway.get_media.assert_called_once_with(1, MediaType.MOVIE, [])
    assert result == sample_media_info_dto


@pytest.mark.asyncio
async def test_get_media_delegates_to_sonarr_for_tv(composite, mock_sonarr_gateway, sample_media_info_dto_tv):
    """Test get_media delegates to SonarrGateway for TV shows."""
    mock_sonarr_gateway.get_media = AsyncMock(return_value=sample_media_info_dto_tv)

    result = await composite.get_media(1, MediaType.TV, [1, 2])

    mock_sonarr_gateway.get_media.assert_called_once_with(1, MediaType.TV, [1, 2])
    assert result == sample_media_info_dto_tv


@pytest.mark.asyncio
async def test_delete_media_delegates_to_radarr_for_movie(composite, mock_radarr_gateway):
    """Test delete_media delegates to RadarrGateway for movies."""
    mock_radarr_gateway.delete_media = AsyncMock()

    await composite.delete_media(1, MediaType.MOVIE, [])

    mock_radarr_gateway.delete_media.assert_called_once_with(1, MediaType.MOVIE, [])


@pytest.mark.asyncio
async def test_delete_media_delegates_to_sonarr_for_tv(composite, mock_sonarr_gateway):
    """Test delete_media delegates to SonarrGateway for TV shows."""
    mock_sonarr_gateway.delete_media = AsyncMock()

    await composite.delete_media(1, MediaType.TV, [1, 2])

    mock_sonarr_gateway.delete_media.assert_called_once_with(1, MediaType.TV, [1, 2])
