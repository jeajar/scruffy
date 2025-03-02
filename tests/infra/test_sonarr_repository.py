import json
from datetime import UTC, datetime

import httpx
import pytest
import respx

from scruffy.infra.data_transfer_objects import MediaInfoDTO
from scruffy.infra.sonarr_repository import SonarrRepository


@pytest.fixture
def base_url():
    return "http://test.com"


@pytest.fixture
def api_key():
    return "test-api-key"


@pytest.fixture
def repo(base_url, api_key):
    return SonarrRepository(base_url, api_key)


@pytest.fixture
def mock_series_response():
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


def test_repository_initialization(base_url, api_key):
    repo = SonarrRepository(base_url, api_key)
    assert repo.base_url == base_url
    assert repo.api_key == api_key
    assert repo.headers == {"X-Api-Key": api_key, "Accept": "application/json"}


def test_get_series_poster():
    repo = SonarrRepository("http://test.com", "test-key")
    images = [
        {"coverType": "poster", "remoteUrl": "http://test.com/poster.jpg"},
        {"coverType": "fanart", "remoteUrl": "http://test.com/fanart.jpg"},
    ]
    assert repo._get_series_poster(images) == "http://test.com/poster.jpg"


def test_get_series_poster_no_poster():
    repo = SonarrRepository("http://test.com", "test-key")
    images = [{"coverType": "fanart", "remoteUrl": "http://test.com/fanart.jpg"}]
    assert repo._get_series_poster(images) is None


@pytest.mark.asyncio
async def test_get_series(repo, base_url, mock_series_response):
    with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.get("/api/v3/series/1").mock(
            return_value=httpx.Response(200, json=mock_series_response)
        )

        result = await repo.get_series(1)
        assert result == mock_series_response


@pytest.mark.asyncio
async def test_get_series_info(
    repo, base_url, mock_series_response, mock_episodes_response
):
    with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.get("/api/v3/series/1").mock(
            return_value=httpx.Response(200, json=mock_series_response)
        )
        respx_mock.get("/api/v3/episode").mock(
            return_value=httpx.Response(200, json=mock_episodes_response)
        )

        result = await repo.get_series_info(1, [1])
        assert isinstance(result, MediaInfoDTO)
        assert result.title == "Test Series"
        assert result.available is True
        assert result.poster == "http://test.com/poster.jpg"
        assert result.available_since == datetime(2024, 1, 2, 12, 0, tzinfo=UTC)
        assert result.size_on_disk == 1000000
        assert result.seasons == [1]


@pytest.mark.asyncio
async def test_get_series_info_unavailable(
    repo, base_url, mock_series_response, mock_episodes_response
):
    mock_episodes_response[0]["hasFile"] = False

    with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.get("/api/v3/series/1").mock(
            return_value=httpx.Response(200, json=mock_series_response)
        )
        respx_mock.get("/api/v3/episode").mock(
            return_value=httpx.Response(200, json=mock_episodes_response)
        )

        result = await repo.get_series_info(1, [1])
        assert result.available is False
        assert result.available_since is None


@pytest.mark.asyncio
async def test_get_episodes(repo, base_url, mock_episodes_response):
    with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.get("/api/v3/episode").mock(
            return_value=httpx.Response(200, json=mock_episodes_response)
        )

        result = await repo.get_episodes(1, 1)
        assert result == mock_episodes_response
        assert dict(respx_mock.calls.last.request.url.params) == {
            "seriesId": "1",
            "seasonNumber": "1",
            "includeEpisodeFile": "true",
        }


@pytest.mark.asyncio
async def test_delete_series_seasons(repo, base_url, mock_series_response):
    mock_episodes_with_files = [
        {
            "seasonNumber": 1,
            "episodeNumber": 1,
            "hasFile": True,
            "episodeFileId": 101,
        }
    ]

    with respx.mock(base_url=base_url) as respx_mock:
        get_series = respx_mock.get("/api/v3/series/1").mock(
            return_value=httpx.Response(200, json=mock_series_response)
        )
        put_series = respx_mock.put("/api/v3/series/1").mock(
            return_value=httpx.Response(200)
        )
        get_episodes = respx_mock.get("/api/v3/episode").mock(
            return_value=httpx.Response(200, json=mock_episodes_with_files)
        )
        delete_file = respx_mock.delete("/api/v3/episodefile/101").mock(
            return_value=httpx.Response(200)
        )

        await repo.delete_series_seasons(1, [1])

        # Verify all expected calls were made
        assert get_series.called
        assert put_series.called
        assert get_episodes.called
        assert delete_file.called

        # Verify the PUT request updated monitoring
        put_request = next(
            call for call in respx_mock.calls if call.request.method == "PUT"
        )
        sent_data = json.loads(put_request.request.read().decode())
        assert sent_data["seasons"][0]["monitored"] is False


@pytest.mark.asyncio
async def test_delete_series_seasons_with_no_remaining_monitored_seasons(
    repo, base_url
):
    """Test that series is deleted when no monitored seasons remain after deletion."""
    series_id = 1
    seasons_to_delete = [1, 2]

    mock_series = {
        "id": series_id,
        "title": "Test Series",
        "seasons": [
            {"seasonNumber": 1, "monitored": False},
            {"seasonNumber": 2, "monitored": False},
        ],
    }

    mock_episodes = [
        {"seasonNumber": 1, "episodeNumber": 1, "hasFile": True, "episodeFileId": 101},
        {"seasonNumber": 2, "episodeNumber": 1, "hasFile": True, "episodeFileId": 201},
    ]

    with respx.mock(base_url=base_url) as respx_mock:
        # Mock initial series get for updating monitoring
        respx_mock.get(f"/api/v3/series/{series_id}").mock(
            return_value=httpx.Response(200, json=mock_series)
        )
        # Mock series update
        respx_mock.put(f"/api/v3/series/{series_id}").mock(
            return_value=httpx.Response(200)
        )
        # Mock episodes get for file deletion
        respx_mock.get("/api/v3/episode").mock(
            return_value=httpx.Response(200, json=mock_episodes)
        )
        # Mock episode file deletions
        respx_mock.delete("/api/v3/episodefile/101").mock(
            return_value=httpx.Response(200)
        )
        respx_mock.delete("/api/v3/episodefile/201").mock(
            return_value=httpx.Response(200)
        )
        # Mock series deletion
        delete_series = respx_mock.delete(f"/api/v3/series/{series_id}").mock(
            return_value=httpx.Response(204)
        )

        await repo.delete_series_seasons(series_id, seasons_to_delete)

        # Verify series was deleted
        assert delete_series.called
        # Verify the deleteFiles parameter was set to False (default value)
        params = dict(delete_series.calls[0].request.url.params)
        assert params["deleteFiles"] == "false"
        # Verify the addImportListExclusion parameter was set to False (default value)
        assert params["addImportListExclusion"] == "false"


@pytest.mark.asyncio
async def test_delete_series_seasons_with_remaining_monitored_seasons(repo, base_url):
    """Test that series is not deleted when monitored seasons remain after deletion."""
    series_id = 1
    seasons_to_delete = [1]

    mock_series = {
        "id": series_id,
        "title": "Test Series",
        "seasons": [
            {"seasonNumber": 1, "monitored": False},
            {"seasonNumber": 2, "monitored": True},  # Season 2 remains monitored
        ],
    }

    mock_episodes = [
        {"seasonNumber": 1, "episodeNumber": 1, "hasFile": True, "episodeFileId": 101}
    ]

    with respx.mock(base_url=base_url, assert_all_called=False) as respx_mock:
        # Mock initial series get for updating monitoring
        respx_mock.get(f"/api/v3/series/{series_id}").mock(
            return_value=httpx.Response(200, json=mock_series)
        )
        # Mock series update
        respx_mock.put(f"/api/v3/series/{series_id}").mock(
            return_value=httpx.Response(200)
        )
        # Mock episodes get for file deletion
        respx_mock.get("/api/v3/episode").mock(
            return_value=httpx.Response(200, json=mock_episodes)
        )
        # Mock episode file deletion
        respx_mock.delete("/api/v3/episodefile/101").mock(
            return_value=httpx.Response(200)
        )
        # Mock series deletion (should not be called)
        delete_series = respx_mock.delete(f"/api/v3/series/{series_id}").mock(
            return_value=httpx.Response(204)
        )

        await repo.delete_series_seasons(series_id, seasons_to_delete)

        # Verify series was not deleted
        assert not delete_series.called


@pytest.mark.asyncio
async def test_delete_season_files(repo, base_url, mock_episodes_response):
    with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.get("/api/v3/episode").mock(
            return_value=httpx.Response(200, json=mock_episodes_response)
        )
        delete_101 = respx_mock.delete("/api/v3/episodefile/101").mock(
            return_value=httpx.Response(200)
        )
        delete_102 = respx_mock.delete("/api/v3/episodefile/102").mock(
            return_value=httpx.Response(200)
        )

        await repo.delete_season_files(1, [1])
        assert delete_101.called
        assert delete_102.called


@pytest.mark.asyncio
async def test_delete_episode_files(repo, base_url):
    with respx.mock(base_url=base_url) as respx_mock:
        delete_101 = respx_mock.delete("/api/v3/episodefile/101").mock(
            return_value=httpx.Response(200)
        )
        delete_102 = respx_mock.delete("/api/v3/episodefile/102").mock(
            return_value=httpx.Response(200)
        )

        await repo.delete_episode_files([101, 102])
        assert delete_101.called
        assert delete_102.called


@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_update_season_monitoring(repo, base_url, mock_series_response):
    with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.get("/api/v3/series/1").mock(
            return_value=httpx.Response(200, json=mock_series_response)
        )
        respx_mock.put("/api/v3/series/1").mock(return_value=httpx.Response(200))

        await repo.update_season_monitoring(1, [1])

        # Verify PUT request
        put_request = next(
            call for call in respx_mock.calls if call.request.method == "PUT"
        )
        sent_data = json.loads(put_request.request.read().decode())

        # Check season monitoring status
        assert sent_data["seasons"][0]["seasonNumber"] == 1
        assert sent_data["seasons"][0]["monitored"] is False
        assert sent_data["seasons"][1]["monitored"] is True
