"""Tests for SonarrGateway."""

from types import SimpleNamespace

import httpx
import pytest
import respx

from scruffy.domain.value_objects.media_type import MediaType
from scruffy.frameworks_and_drivers.http.http_client import HttpClient
from scruffy.interface_adapters.gateways.sonarr_gateway import SonarrGateway


def _make_settings_provider(base_url: str, api_key: str):
    """Create mock SettingsProvider returning given url/api_key for Sonarr."""
    config = SimpleNamespace(
        overseerr_url="http://test.com",
        overseerr_api_key="test-key",
        radarr_url="http://test.com",
        radarr_api_key="test-key",
        sonarr_url=base_url,
        sonarr_api_key=api_key,
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
    """Create SonarrGateway instance."""
    return SonarrGateway(_make_settings_provider(base_url, api_key), HttpClient())


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
        respx_mock.get("/api/v3/system/status").mock(return_value=httpx.Response(500))

        result = await gateway.status()

        assert result is False


@pytest.fixture
def mock_series_response():
    """Mock series response."""
    return {
        "id": 1,
        "title": "Test Series",
        "images": [{"coverType": "poster", "remoteUrl": "http://test.com/poster.jpg"}],
        "seasons": [
            {"seasonNumber": 1, "monitored": True},
            {"seasonNumber": 2, "monitored": True},
        ],
    }


@pytest.fixture
def mock_episodes_response():
    """Mock episodes response."""
    return [
        {
            "seasonNumber": 1,
            "episodeNumber": 1,
            "hasFile": True,
            "episodeFileId": 101,
            "episodeFile": {
                "dateAdded": "2024-01-01T12:00:00Z",
                "size": 500000,
            },
        },
        {
            "seasonNumber": 1,
            "episodeNumber": 2,
            "hasFile": True,
            "episodeFileId": 102,
            "episodeFile": {
                "dateAdded": "2024-01-02T12:00:00Z",
                "size": 500000,
            },
        },
    ]


@pytest.mark.asyncio
async def test_get_media_complete(
    gateway, base_url, mock_series_response, mock_episodes_response
):
    """Test get_media returns complete MediaInfoDTO."""
    with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.get("/api/v3/series/1").mock(
            return_value=httpx.Response(200, json=mock_series_response)
        )
        respx_mock.get("/api/v3/episode").mock(
            return_value=httpx.Response(200, json=mock_episodes_response)
        )

        result = await gateway.get_media(1, MediaType.TV, [1])

        assert result.title == "Test Series"
        assert result.available is True
        assert result.poster == "http://test.com/poster.jpg"
        assert result.size_on_disk == 1000000
        assert result.seasons == [1]


@pytest.mark.asyncio
async def test_get_media_unavailable(gateway, base_url, mock_series_response):
    """Test get_media handles unavailable episodes."""
    unavailable_episodes = [
        {
            "seasonNumber": 1,
            "episodeNumber": 1,
            "hasFile": False,
        }
    ]

    with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.get("/api/v3/series/1").mock(
            return_value=httpx.Response(200, json=mock_series_response)
        )
        respx_mock.get("/api/v3/episode").mock(
            return_value=httpx.Response(200, json=unavailable_episodes)
        )

        result = await gateway.get_media(1, MediaType.TV, [1])

        assert result.available is False
        assert result.available_since is None


@pytest.mark.asyncio
async def test_get_media_raises_for_movie(gateway):
    """Test get_media raises ValueError for movie type."""
    with pytest.raises(ValueError, match="SonarrGateway only handles TV shows"):
        await gateway.get_media(1, MediaType.MOVIE, [])


@pytest.mark.asyncio
async def test_delete_media(gateway, base_url, mock_series_response):
    """Test delete_media deletes seasons."""
    mock_episodes = [
        {
            "seasonNumber": 1,
            "episodeNumber": 1,
            "hasFile": True,
            "episodeFileId": 101,
        }
    ]

    with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.get("/api/v3/series/1").mock(
            return_value=httpx.Response(200, json=mock_series_response)
        )
        respx_mock.put("/api/v3/series/1").mock(
            return_value=httpx.Response(200, json=mock_series_response)
        )
        respx_mock.get("/api/v3/episode").mock(
            return_value=httpx.Response(200, json=mock_episodes)
        )
        respx_mock.delete("/api/v3/episodefile/101").mock(
            return_value=httpx.Response(200)
        )

        await gateway.delete_media(1, MediaType.TV, [1])

        # Verify monitoring was updated and files deleted
        assert any(call.request.method == "PUT" for call in respx_mock.calls)
        assert any(
            call.request.url.path == "/api/v3/episodefile/101"
            for call in respx_mock.calls
        )


@pytest.mark.asyncio
async def test_delete_media_raises_for_movie(gateway):
    """Test delete_media raises ValueError for movie type."""
    with pytest.raises(ValueError, match="SonarrGateway only handles TV shows"):
        await gateway.delete_media(1, MediaType.MOVIE, [])


@pytest.mark.asyncio
async def test_get_series(gateway, base_url, mock_series_response):
    """Test get_series retrieves series information."""
    with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.get("/api/v3/series/1").mock(
            return_value=httpx.Response(200, json=mock_series_response)
        )

        result = await gateway.get_series(1)

        assert result == mock_series_response


@pytest.mark.asyncio
async def test_get_episodes(gateway, base_url, mock_episodes_response):
    """Test get_episodes retrieves episodes for season."""
    with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.get("/api/v3/episode").mock(
            return_value=httpx.Response(200, json=mock_episodes_response)
        )

        result = await gateway.get_episodes(1, 1)

        assert result == mock_episodes_response
        # Verify query parameters
        params = dict(respx_mock.calls.last.request.url.params)
        assert params["seriesId"] == "1"
        assert params["seasonNumber"] == "1"


@pytest.mark.asyncio
async def test_delete_season_files(gateway, base_url, mock_episodes_response):
    """Test delete_season_files deletes episode files."""
    with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.get("/api/v3/episode").mock(
            return_value=httpx.Response(200, json=mock_episodes_response)
        )
        respx_mock.delete("/api/v3/episodefile/101").mock(
            return_value=httpx.Response(200)
        )
        respx_mock.delete("/api/v3/episodefile/102").mock(
            return_value=httpx.Response(200)
        )

        await gateway.delete_season_files(1, [1])

        # Verify both episode files were deleted
        delete_calls = [
            call for call in respx_mock.calls if call.request.method == "DELETE"
        ]
        assert len(delete_calls) == 2


@pytest.mark.asyncio
async def test_update_season_monitoring(gateway, base_url, mock_series_response):
    """Test update_season_monitoring updates monitoring status."""
    with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.get("/api/v3/series/1").mock(
            return_value=httpx.Response(200, json=mock_series_response)
        )
        respx_mock.put("/api/v3/series/1").mock(
            return_value=httpx.Response(200, json=mock_series_response)
        )

        await gateway.update_season_monitoring(1, [1])

        # Verify PUT was called
        put_call = next(
            call for call in respx_mock.calls if call.request.method == "PUT"
        )
        assert put_call is not None


@pytest.mark.asyncio
async def test_delete_empty_series(gateway, base_url):
    """Test _delete_empty_series deletes series when all seasons unmonitored."""
    series_with_unmonitored = {
        "id": 1,
        "title": "Test Series",
        "seasons": [
            {"seasonNumber": 1, "monitored": False},
            {"seasonNumber": 2, "monitored": False},
        ],
    }

    with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.get("/api/v3/series/1").mock(
            return_value=httpx.Response(200, json=series_with_unmonitored)
        )
        respx_mock.delete("/api/v3/series/1").mock(return_value=httpx.Response(204))

        await gateway._delete_empty_series(1)

        assert any(
            call.request.url.path == "/api/v3/series/1"
            for call in respx_mock.calls
            if call.request.method == "DELETE"
        )


def test_get_series_poster():
    """Test _get_series_poster extracts poster URL."""
    gateway = SonarrGateway(
        _make_settings_provider("http://test.com", "test-key"),
        HttpClient(),
    )
    images = [
        {"coverType": "poster", "remoteUrl": "http://test.com/poster.jpg"},
        {"coverType": "fanart", "remoteUrl": "http://test.com/fanart.jpg"},
    ]

    poster = gateway._get_series_poster(images)

    assert poster == "http://test.com/poster.jpg"


def test_get_series_poster_no_poster():
    """Test _get_series_poster returns None when no poster."""
    gateway = SonarrGateway(
        _make_settings_provider("http://test.com", "test-key"),
        HttpClient(),
    )
    images = [{"coverType": "fanart", "remoteUrl": "http://test.com/fanart.jpg"}]

    poster = gateway._get_series_poster(images)

    assert poster is None


def test_gateway_initialization(base_url, api_key):
    """Test gateway initialization with settings provider."""
    provider = _make_settings_provider(base_url, api_key)
    http_client = HttpClient()
    gateway = SonarrGateway(provider, http_client)

    assert gateway._settings_provider is provider
    assert gateway.http_client is http_client
