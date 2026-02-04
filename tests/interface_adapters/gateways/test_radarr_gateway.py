"""Tests for RadarrGateway."""

from types import SimpleNamespace

import httpx
import pytest
import respx

from scruffy.domain.value_objects.media_type import MediaType
from scruffy.frameworks_and_drivers.http.http_client import HttpClient
from scruffy.interface_adapters.gateways.radarr_gateway import RadarrGateway


def _make_settings_provider(base_url: str, api_key: str):
    """Create mock SettingsProvider returning given url/api_key for Radarr."""
    config = SimpleNamespace(
        overseerr_url="http://test.com",
        overseerr_api_key="test-key",
        radarr_url=base_url,
        radarr_api_key=api_key,
        sonarr_url="http://test.com",
        sonarr_api_key="test-key",
    )
    provider = SimpleNamespace()
    provider.get_services_config = lambda: config
    return provider


@pytest.fixture
def base_url():
    """Base URL for testing."""
    return "http://test.com"


@pytest.fixture
def api_key():
    """API key for testing."""
    return "test-api-key"


@pytest.fixture
def gateway(base_url, api_key):
    """Create RadarrGateway instance."""
    return RadarrGateway(_make_settings_provider(base_url, api_key))


@pytest.mark.asyncio
async def test_status_success(gateway, base_url):
    """Test status returns True on successful connection."""
    with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.get("/api/v3/system/status").mock(
            return_value=httpx.Response(200, json={"version": "4.0.0"})
        )

        result = await gateway.status()

        assert result is True


@pytest.mark.asyncio
async def test_status_failure(gateway, base_url):
    """Test status returns False on connection failure."""
    with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.get("/api/v3/system/status").mock(
            return_value=httpx.Response(500)
        )

        result = await gateway.status()

        assert result is False


@pytest.mark.asyncio
async def test_get_media_complete(gateway, base_url):
    """Test get_media returns complete MediaInfoDTO."""
    mock_response = {
        "id": 1,
        "title": "Test Movie",
        "hasFile": True,
        "sizeOnDisk": 1000000,
        "images": [{"coverType": "poster", "remoteUrl": "http://test.com/poster.jpg"}],
        "movieFile": {"dateAdded": "2024-01-01T12:00:00Z"},
    }

    with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.get("/api/v3/movie/1").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        result = await gateway.get_media(1, MediaType.MOVIE, [])

        assert result.title == "Test Movie"
        assert result.available is True
        assert result.poster == "http://test.com/poster.jpg"
        assert result.size_on_disk == 1000000
        assert result.id == 1
        assert result.seasons == []


@pytest.mark.asyncio
async def test_get_media_minimal(gateway, base_url):
    """Test get_media handles minimal response."""
    mock_response = {
        "id": 1,
        "title": "Test Movie",
        "hasFile": False,
        "sizeOnDisk": 0,
        "images": [],
    }

    with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.get("/api/v3/movie/1").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        result = await gateway.get_media(1, MediaType.MOVIE, [])

        assert result.title == "Test Movie"
        assert result.available is False
        assert result.poster == ""
        assert result.available_since is None
        assert result.size_on_disk == 0


@pytest.mark.asyncio
async def test_get_media_raises_for_tv(gateway):
    """Test get_media raises ValueError for TV type."""
    with pytest.raises(ValueError, match="RadarrGateway only handles movies"):
        await gateway.get_media(1, MediaType.TV, [])


@pytest.mark.asyncio
async def test_delete_media(gateway, base_url):
    """Test delete_media deletes movie."""
    with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.delete("/api/v3/movie/1").mock(
            return_value=httpx.Response(200, json={})
        )

        await gateway.delete_media(1, MediaType.MOVIE, [])

        assert respx_mock.calls.last.request.url.path == "/api/v3/movie/1"
        assert "deleteFiles=true" in str(respx_mock.calls.last.request.url.query)


@pytest.mark.asyncio
async def test_delete_media_raises_for_tv(gateway):
    """Test delete_media raises ValueError for TV type."""
    with pytest.raises(ValueError, match="RadarrGateway only handles movies"):
        await gateway.delete_media(1, MediaType.TV, [])


def test_get_movie_poster():
    """Test _get_movie_poster extracts poster URL."""
    gateway = RadarrGateway("http://test.com", "test-key")
    images = [
        {"coverType": "poster", "remoteUrl": "http://test.com/poster.jpg"},
        {"coverType": "fanart", "remoteUrl": "http://test.com/fanart.jpg"},
    ]

    poster = gateway._get_movie_poster(images)

    assert poster == "http://test.com/poster.jpg"


def test_get_movie_poster_no_poster():
    """Test _get_movie_poster returns None when no poster."""
    gateway = RadarrGateway("http://test.com", "test-key")
    images = [{"coverType": "fanart", "remoteUrl": "http://test.com/fanart.jpg"}]

    poster = gateway._get_movie_poster(images)

    assert poster is None


def test_get_movie_poster_empty_images():
    """Test _get_movie_poster returns None for empty images."""
    gateway = RadarrGateway("http://test.com", "test-key")

    poster = gateway._get_movie_poster([])

    assert poster is None


def test_gateway_initialization(base_url, api_key):
    """Test gateway initialization with settings provider."""
    provider = _make_settings_provider(base_url, api_key)
    gateway = RadarrGateway(provider)

    assert gateway._settings_provider is provider
    assert gateway.http_client is not None
