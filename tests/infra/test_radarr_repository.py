from datetime import UTC, datetime

import httpx
import pytest
import respx

from scruffy.infra.data_transfer_objects import MediaInfoDTO
from scruffy.infra.radarr_repository import RadarrRepository


@pytest.fixture
def base_url():
    return "http://test.com"


@pytest.fixture
def api_key():
    return "test-api-key"


@pytest.fixture
def repo(base_url, api_key):
    return RadarrRepository(base_url, api_key)


@pytest.fixture
def mock_movie_response():
    return {
        "id": 1,
        "title": "Test Movie",
        "hasFile": True,
        "sizeOnDisk": 1000000,
        "images": [{"coverType": "poster", "remoteUrl": "http://test.com/poster.jpg"}],
        "movieFile": {"dateAdded": "2024-01-01T12:00:00Z"},
    }


def test_repository_initialization(base_url, api_key):
    repo = RadarrRepository(base_url, api_key)
    assert repo.base_url == base_url
    assert repo.api_key == api_key
    assert repo.headers == {"X-Api-Key": api_key, "Accept": "application/json"}


def test_get_movie_poster():
    repo = RadarrRepository("http://test.com", "test-key")
    images = [
        {"coverType": "poster", "remoteUrl": "http://test.com/poster.jpg"},
        {"coverType": "fanart", "remoteUrl": "http://test.com/fanart.jpg"},
    ]
    assert repo._get_movie_poster(images) == "http://test.com/poster.jpg"


def test_get_movie_poster_no_poster():
    repo = RadarrRepository("http://test.com", "test-key")
    images = [{"coverType": "fanart", "remoteUrl": "http://test.com/fanart.jpg"}]
    assert repo._get_movie_poster(images) is None


def test_get_movie_poster_empty_images():
    repo = RadarrRepository("http://test.com", "test-key")
    assert repo._get_movie_poster([]) is None


@pytest.mark.asyncio
async def test_get_movie_complete(repo, base_url, mock_movie_response):
    with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.get("/api/v3/movie/1").mock(
            return_value=httpx.Response(200, json=mock_movie_response)
        )

        result = await repo.get_movie(1)
        assert isinstance(result, MediaInfoDTO)
        assert result.title == "Test Movie"
        assert result.available is True
        assert result.poster == "http://test.com/poster.jpg"
        assert result.available_since == datetime(2024, 1, 1, 12, 0, tzinfo=UTC)
        assert result.size_on_disk == 1000000
        assert result.id == 1
        assert result.seasons == []


@pytest.mark.asyncio
async def test_get_movie_minimal(repo, base_url):
    minimal_response = {
        "id": 1,
        "title": "Test Movie",
        "hasFile": False,
        "sizeOnDisk": 0,
        "images": [],
    }

    with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.get("/api/v3/movie/1").mock(
            return_value=httpx.Response(200, json=minimal_response)
        )

        result = await repo.get_movie(1)
        assert result.title == "Test Movie"
        assert result.available is False
        assert result.poster is None
        assert result.available_since is None
        assert result.size_on_disk == 0


@pytest.mark.asyncio
async def test_get_movie_http_error(repo, base_url):
    with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.get("/api/v3/movie/1").mock(return_value=httpx.Response(404))

        with pytest.raises(httpx.HTTPError):
            await repo.get_movie(1)


@pytest.mark.asyncio
async def test_delete_movie(repo, base_url):
    with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.delete("/api/v3/movie/1").mock(
            return_value=httpx.Response(200, json={})
        )

        await repo.delete_movie(1)
        assert respx_mock.calls.last.request.url.path == "/api/v3/movie/1"
        assert respx_mock.calls.last.request.url.query == b"deleteFiles=true"


@pytest.mark.asyncio
async def test_delete_movie_without_files(repo, base_url):
    with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.delete("/api/v3/movie/1").mock(
            return_value=httpx.Response(200, json={})
        )

        await repo.delete_movie(1, delete_files=False)
        assert respx_mock.calls.last.request.url.query == b"deleteFiles=false"


@pytest.mark.asyncio
async def test_delete_movie_http_error(repo, base_url):
    with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.delete("/api/v3/movie/1").mock(return_value=httpx.Response(500))

        with pytest.raises(httpx.HTTPError):
            await repo.delete_movie(1)
