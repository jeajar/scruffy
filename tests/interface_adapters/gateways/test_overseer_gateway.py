"""Tests for OverseerGateway."""

from types import SimpleNamespace

import httpx
import pytest
import respx

from scruffy.frameworks_and_drivers.http.http_client import HttpClient
from scruffy.interface_adapters.gateways.overseer_gateway import OverseerGateway
from scruffy.interface_adapters.interfaces.http_client_interface import (
    HttpRequestError,
)


def _make_settings_provider(base_url: str, api_key: str):
    """Create mock SettingsProvider returning given url/api_key for Overseerr."""
    config = SimpleNamespace(
        overseerr_url=base_url,
        overseerr_api_key=api_key,
        radarr_url="http://test.com",
        radarr_api_key="test-key",
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
    """Create OverseerGateway instance."""
    return OverseerGateway(
        _make_settings_provider(base_url, api_key), HttpClient()
    )


@pytest.fixture
def gateway_with_http_client(base_url, api_key, mock_http_client):
    """Create OverseerGateway with mocked HTTP client."""
    return OverseerGateway(
        _make_settings_provider(base_url, api_key), mock_http_client
    )


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
        respx_mock.get("/api/v1/status").mock(return_value=httpx.Response(500))

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
        # Count is not called when first page has pageInfo.total
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
    # Implementation uses take=100, so we need total > 100 to trigger pagination
    page1_response = {
        "pageInfo": {"pages": 2, "pageSize": 100, "results": 100, "total": 101},
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
        "pageInfo": {"pages": 2, "pageSize": 100, "results": 1, "total": 101},
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
        # Count is not called when first page has pageInfo.total
        respx_mock.get("/api/v1/request").mock(
            side_effect=[
                httpx.Response(200, json=page1_response),
                httpx.Response(200, json=page2_response),
            ]
        )

        requests = await gateway.get_requests()

        # We get 1 result from page 1 and 1 from page 2 (mocked responses only have 1 each)
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
    """Test gateway initialization with settings provider."""
    provider = _make_settings_provider(base_url, api_key)
    http_client = HttpClient()
    gateway = OverseerGateway(provider, http_client)

    assert gateway._settings_provider is provider
    assert gateway.http_client is http_client


def test_gateway_initialization_with_http_client(base_url, api_key, mock_http_client):
    """Test gateway initialization with custom HTTP client."""
    provider = _make_settings_provider(base_url, api_key)
    gateway = OverseerGateway(provider, mock_http_client)

    assert gateway.http_client == mock_http_client


@pytest.mark.asyncio
async def test_user_imported_by_plex_id_found(gateway, base_url):
    """Test user_imported_by_plex_id returns True when user is in Overseerr."""
    mock_response = {
        "pageInfo": {"pages": 1, "pageSize": 100, "results": 2, "total": 2},
        "results": [
            {"id": 1, "plexId": 100, "username": "other"},
            {"id": 2, "plexId": 42, "username": "target"},
        ],
    }
    with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.get("/api/v1/user").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        result = await gateway.user_imported_by_plex_id(42)

        assert result is True


@pytest.mark.asyncio
async def test_user_imported_by_plex_id_not_found(gateway, base_url):
    """Test user_imported_by_plex_id returns False when user is not in Overseerr."""
    mock_response = {
        "pageInfo": {"pages": 1, "pageSize": 100, "results": 1, "total": 1},
        "results": [{"id": 1, "plexId": 100, "username": "other"}],
    }
    with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.get("/api/v1/user").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        result = await gateway.user_imported_by_plex_id(999)

        assert result is False


@pytest.mark.asyncio
async def test_user_imported_by_plex_id_found_on_second_page(gateway, base_url):
    """Test user_imported_by_plex_id finds user on paginated second page."""
    page1 = {
        "pageInfo": {"pages": 2, "pageSize": 100, "results": 100, "total": 101},
        "results": [
            {"id": i, "plexId": i + 1000, "username": f"u{i}"} for i in range(100)
        ],
    }
    page2 = {
        "pageInfo": {"pages": 2, "pageSize": 100, "results": 1, "total": 101},
        "results": [{"id": 100, "plexId": 42, "username": "target"}],
    }
    with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.get("/api/v1/user").mock(
            side_effect=[
                httpx.Response(200, json=page1),
                httpx.Response(200, json=page2),
            ]
        )

        result = await gateway.user_imported_by_plex_id(42)

        assert result is True


@pytest.mark.asyncio
async def test_user_imported_by_plex_id_api_error(gateway, base_url):
    """Test user_imported_by_plex_id raises when Overseerr API fails."""
    with respx.mock(base_url=base_url) as respx_mock:
        respx_mock.get("/api/v1/user").mock(return_value=httpx.Response(502))

        with pytest.raises(HttpRequestError):
            await gateway.user_imported_by_plex_id(1)
