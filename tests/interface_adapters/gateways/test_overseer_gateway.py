"""Tests for OverseerGateway."""

import httpx
import pytest
import respx

from scruffy.frameworks_and_drivers.http.http_client import HttpClient
from scruffy.interface_adapters.gateways.overseer_gateway import OverseerGateway


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
    """Create OverseerGateway instance."""
    return OverseerGateway(base_url, api_key)


@pytest.fixture
def gateway_with_http_client(base_url, api_key, mock_http_client):
    """Create OverseerGateway with mocked HTTP client."""
    return OverseerGateway(base_url, api_key, mock_http_client)


@pytest.mark.asyncio
async def test_status_success(gateway, base_url):
    """Test status returns True on successful connection."""
    with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.get("/api/v1/status").mock(
            return_value=httpx.Response(200, json={"status": "ok"})
        )

        result = await gateway.status()

        assert result is True


@pytest.mark.asyncio
async def test_status_failure(gateway, base_url):
    """Test status returns False on connection failure."""
    with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.get("/api/v1/status").mock(
            return_value=httpx.Response(500)
        )

        result = await gateway.status()

        assert result is False


@pytest.mark.asyncio
async def test_get_requests_single_page(gateway, base_url):
    """Test get_requests handles single page of results."""
    mock_response = {
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
                "status": "approved",
                "requestedBy": {"id": 1, "email": "test@example.com"},
                "media": {
                    "status": "available",
                    "externalServiceId": 1000,
                    "updatedAt": "2023-01-01T12:00:00Z",
                    "id": 99,
                },
            }
        ],
    }

    with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.get("/api/v1/request/count").mock(
            return_value=httpx.Response(200, json={"total": 1})
        )
        respx_mock.get("/api/v1/request").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        requests = await gateway.get_requests()

        assert len(requests) == 1
        assert requests[0].request_id == 1
        assert requests[0].user_email == "test@example.com"


@pytest.mark.asyncio
async def test_get_requests_pagination(gateway, base_url):
    """Test get_requests handles pagination correctly."""
    page1_response = {
        "pageInfo": {"pages": 2, "pageSize": 1, "results": 1, "total": 2},
        "results": [
            {
                "id": 1,
                "type": "movie",
                "status": "approved",
                "requestedBy": {"id": 1, "email": "test1@example.com"},
                "media": {
                    "status": "available",
                    "externalServiceId": 1000,
                    "updatedAt": "2023-01-01T12:00:00Z",
                    "id": 99,
                },
            }
        ],
    }
    page2_response = {
        "pageInfo": {"pages": 2, "pageSize": 1, "results": 1, "total": 2},
        "results": [
            {
                "id": 2,
                "type": "movie",
                "status": "approved",
                "requestedBy": {"id": 2, "email": "test2@example.com"},
                "media": {
                    "status": "available",
                    "externalServiceId": 1001,
                    "updatedAt": "2023-01-02T12:00:00Z",
                    "id": 100,
                },
            }
        ],
    }

    with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.get("/api/v1/request/count").mock(
            return_value=httpx.Response(200, json={"total": 2})
        )
        respx_mock.get("/api/v1/request").mock(side_effect=[
            httpx.Response(200, json=page1_response),
            httpx.Response(200, json=page2_response),
        ])

        requests = await gateway.get_requests()

        assert len(requests) == 2
        assert requests[0].request_id == 1
        assert requests[1].request_id == 2


@pytest.mark.asyncio
async def test_delete_request(gateway, base_url):
    """Test delete_request deletes request by ID."""
    with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.delete("/api/v1/request/1").mock(
            return_value=httpx.Response(200, json={})
        )

        await gateway.delete_request(1)

        assert respx_mock.calls.last.request.url.path == "/api/v1/request/1"


@pytest.mark.asyncio
async def test_delete_media(gateway, base_url):
    """Test delete_media deletes media by ID."""
    with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.delete("/api/v1/media/1").mock(
            return_value=httpx.Response(200, json={})
        )

        await gateway.delete_media(1)

        assert respx_mock.calls.last.request.url.path == "/api/v1/media/1"


@pytest.mark.asyncio
async def test_get_request_count(gateway, base_url):
    """Test get_request_count returns total count."""
    with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.get("/api/v1/request/count").mock(
            return_value=httpx.Response(200, json={"total": 42})
        )

        count = await gateway.get_request_count()

        assert count == 42


def test_gateway_initialization(base_url, api_key):
    """Test gateway initialization sets correct attributes."""
    gateway = OverseerGateway(base_url, api_key)

    assert gateway.base_url == base_url
    assert gateway.api_key == api_key
    assert gateway.headers == {"X-Api-Key": api_key, "Accept": "application/json"}


def test_gateway_initialization_with_http_client(base_url, api_key, mock_http_client):
    """Test gateway initialization with custom HTTP client."""
    gateway = OverseerGateway(base_url, api_key, mock_http_client)

    assert gateway.http_client == mock_http_client
