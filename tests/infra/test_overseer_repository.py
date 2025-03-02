import httpx
import pytest
import respx

from scruffy.infra.overseer_repository import OverseerRepository


@pytest.fixture
def base_url():
    return "http://test.com"


@pytest.fixture
def api_key():
    return "test-api-key"


@pytest.fixture
def repo(base_url, api_key):
    return OverseerRepository(base_url, api_key)


@pytest.fixture
def mock_request_response():
    return {
        "pageInfo": {
            "pages": 1,
            "pageSize": 10,
            "results": 1,
            "total": 1,
        },
        "results": [
            {
                "id": 1,
                "type": "movie",
                "status": 1,
                "requestedBy": {"id": 1, "email": "test@example.com"},
                "media": {
                    "status": 1,
                    "externalServiceId": 1000,
                    "updatedAt": "2023-01-01T12:00:00",
                },
            }
        ],
    }


@pytest.mark.asyncio
async def test_status(repo, base_url):
    with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.get("/api/v1/status").mock(
            return_value=httpx.Response(200, json={"status": "ok"})
        )

        status = await repo.status()
        assert status


@pytest.mark.asyncio
async def test_get_requests(repo, base_url, mock_request_response):
    with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.get("/api/v1/request/count").mock(
            return_value=httpx.Response(200, json={"total": 1})
        )
        respx_mock.get("/api/v1/request").mock(
            return_value=httpx.Response(200, json=mock_request_response)
        )

        requests = await repo.get_requests()
        assert len(requests) == 1
        assert requests[0].request_id == 1
        assert requests[0].user_email == "test@example.com"


@pytest.mark.asyncio
async def test_delete_request(repo, base_url):
    with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.delete("/api/v1/request/1").mock(
            return_value=httpx.Response(200, json={})
        )

        await repo.delete_request(1)
        assert respx_mock.calls.last.request.url.path == "/api/v1/request/1"


@pytest.mark.asyncio
async def test_delete_media(repo, base_url):
    with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.delete("/api/v1/media/1").mock(
            return_value=httpx.Response(200, json={})
        )

        await repo.delete_media(1)
        assert respx_mock.calls.last.request.url.path == "/api/v1/media/1"


@pytest.mark.asyncio
async def test_get_media_info(repo, base_url):
    mock_media = {"id": 1, "title": "Test Movie"}
    with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.get("/api/v1/media/1").mock(
            return_value=httpx.Response(200, json=mock_media)
        )

        result = await repo.get_media_info(1)
        assert result == mock_media


@pytest.mark.asyncio
async def test_get_request_count(repo, base_url):
    with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.get("/api/v1/request/count").mock(
            return_value=httpx.Response(200, json={"total": 42})
        )

        count = await repo.get_request_count()
        assert count == 42


@pytest.mark.asyncio
async def test_get_main_settings(repo, base_url):
    mock_settings = {"apiKey": "test-key"}
    with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.get("/api/v1/settings/main").mock(
            return_value=httpx.Response(200, json=mock_settings)
        )

        settings = await repo.get_main_settings()
        assert settings == mock_settings


def test_repository_initialization(base_url, api_key):
    repo = OverseerRepository(base_url, api_key)
    assert repo.base_url == base_url
    assert repo.api_key == api_key
    assert repo.headers == {"X-Api-Key": api_key, "Accept": "application/json"}
