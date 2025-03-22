import httpx
import pytest
import respx

from scruffy.frameworks_and_drivers.api_clients.overseerr_client import OverseerrClient


@pytest.fixture
def base_url():
    return "http://test.com"


@pytest.fixture
def api_key():
    return "test-api-key"


@pytest.fixture
def client(base_url, api_key):
    return OverseerrClient(base_url, api_key)


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
async def test_status(client, base_url):
    with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.get("/api/v1/status").mock(
            return_value=httpx.Response(200, json={"status": "ok"})
        )

        status = await client.status()
        assert status


@pytest.mark.asyncio
async def test_get_requests(client, base_url, mock_request_response):
    with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.get("/api/v1/request/count").mock(
            return_value=httpx.Response(200, json={"total": 1})
        )
        respx_mock.get("/api/v1/request").mock(
            return_value=httpx.Response(200, json=mock_request_response)
        )

        requests = await client.get_requests()
        assert len(requests) == 1
        assert requests[0].request_id == 1
        assert requests[0].user_email == "test@example.com"


@pytest.mark.asyncio
async def test_delete_request(client, base_url):
    with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.delete("/api/v1/request/1").mock(
            return_value=httpx.Response(200, json={})
        )

        await client.delete_request(1)
        assert respx_mock.calls.last.request.url.path == "/api/v1/request/1"


@pytest.mark.asyncio
async def test_delete_media(client, base_url):
    with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.delete("/api/v1/media/1").mock(
            return_value=httpx.Response(200, json={})
        )

        await client.delete_media(1)
        assert respx_mock.calls.last.request.url.path == "/api/v1/media/1"


@pytest.mark.asyncio
async def test_get_media_info(client, base_url):
    mock_media = {"id": 1, "title": "Test Movie"}
    with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.get("/api/v1/media/1").mock(
            return_value=httpx.Response(200, json=mock_media)
        )

        result = await client.get_media_info(1)
        assert result == mock_media


@pytest.mark.asyncio
async def test_get_request_count(client, base_url):
    with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.get("/api/v1/request/count").mock(
            return_value=httpx.Response(200, json={"total": 42})
        )

        count = await client.get_request_count()
        assert count == 42


@pytest.mark.asyncio
async def test_get_main_settings(client, base_url):
    mock_settings = {"apiKey": "test-key"}
    with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.get("/api/v1/settings/main").mock(
            return_value=httpx.Response(200, json=mock_settings)
        )

        settings = await client.get_main_settings()
        assert settings == mock_settings


def test_clientsitory_initialization(base_url, api_key):
    client = OverseerrClient(base_url, api_key)
    assert client.base_url == base_url
    assert client.api_key == api_key
    assert client.headers == {"X-Api-Key": api_key, "Accept": "application/json"}
