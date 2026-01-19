"""Tests for HttpClient."""

import httpx
import pytest
import respx

from scruffy.frameworks_and_drivers.http.http_client import HttpClient


@pytest.fixture
def client():
    """Create HttpClient instance."""
    return HttpClient()


class TestHttpClientGet:
    """Tests for HttpClient GET method."""

    @pytest.mark.asyncio
    async def test_get_success(self, client):
        """Test get makes successful GET request."""
        with respx.mock:
            respx.get("http://test.com/api").mock(
                return_value=httpx.Response(200, json={"status": "ok"})
            )

            result = await client.get("http://test.com/api")

            assert result == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_get_with_headers(self, client):
        """Test get includes headers in request."""
        with respx.mock:
            respx.get("http://test.com/api").mock(
                return_value=httpx.Response(200, json={"status": "ok"})
            )

            await client.get("http://test.com/api", headers={"X-API-Key": "test-key"})

            # Verify headers were sent
            assert respx.calls.last.request.headers["X-API-Key"] == "test-key"

    @pytest.mark.asyncio
    async def test_get_with_params(self, client):
        """Test get includes query parameters."""
        with respx.mock:
            respx.get("http://test.com/api").mock(
                return_value=httpx.Response(200, json={"status": "ok"})
            )

            await client.get("http://test.com/api", params={"page": "1", "limit": "10"})

            # Verify params were sent
            assert "page=1" in str(respx.calls.last.request.url)
            assert "limit=10" in str(respx.calls.last.request.url)

    @pytest.mark.asyncio
    async def test_get_raises_on_error(self, client):
        """Test get raises HTTPError on HTTP error."""
        with respx.mock:
            respx.get("http://test.com/api").mock(return_value=httpx.Response(404))

            with pytest.raises(httpx.HTTPStatusError):
                await client.get("http://test.com/api")


class TestHttpClientDelete:
    """Tests for HttpClient DELETE method."""

    @pytest.mark.asyncio
    async def test_delete_success(self, client):
        """Test delete makes successful DELETE request."""
        with respx.mock:
            respx.delete("http://test.com/api/resource/1").mock(
                return_value=httpx.Response(200)
            )

            # Should not raise
            await client.delete("http://test.com/api/resource/1")

    @pytest.mark.asyncio
    async def test_delete_with_headers(self, client):
        """Test delete includes headers in request."""
        with respx.mock:
            respx.delete("http://test.com/api/resource/1").mock(
                return_value=httpx.Response(200)
            )

            await client.delete(
                "http://test.com/api/resource/1", headers={"X-API-Key": "test-key"}
            )

            assert respx.calls.last.request.headers["X-API-Key"] == "test-key"

    @pytest.mark.asyncio
    async def test_delete_with_params(self, client):
        """Test delete includes query parameters."""
        with respx.mock:
            respx.delete("http://test.com/api/resource/1").mock(
                return_value=httpx.Response(200)
            )

            await client.delete(
                "http://test.com/api/resource/1", params={"deleteFiles": "true"}
            )

            assert "deleteFiles=true" in str(respx.calls.last.request.url)

    @pytest.mark.asyncio
    async def test_delete_raises_on_error(self, client):
        """Test delete raises HTTPError on HTTP error."""
        with respx.mock:
            respx.delete("http://test.com/api/resource/1").mock(
                return_value=httpx.Response(500)
            )

            with pytest.raises(httpx.HTTPStatusError):
                await client.delete("http://test.com/api/resource/1")


class TestHttpClientPut:
    """Tests for HttpClient PUT method."""

    @pytest.mark.asyncio
    async def test_put_success(self, client):
        """Test put makes successful PUT request."""
        with respx.mock:
            respx.put("http://test.com/api/resource/1").mock(
                return_value=httpx.Response(200, json={"id": 1, "updated": True})
            )

            result = await client.put(
                "http://test.com/api/resource/1", json={"name": "test"}
            )

            assert result == {"id": 1, "updated": True}

    @pytest.mark.asyncio
    async def test_put_with_json(self, client):
        """Test put sends JSON body."""
        with respx.mock:
            respx.put("http://test.com/api/resource/1").mock(
                return_value=httpx.Response(200, json={"status": "ok"})
            )

            await client.put(
                "http://test.com/api/resource/1", json={"name": "test", "value": 123}
            )

            # Verify JSON was sent
            request_body = respx.calls.last.request.read()
            assert b"name" in request_body
            assert b"test" in request_body

    @pytest.mark.asyncio
    async def test_put_with_headers(self, client):
        """Test put includes headers in request."""
        with respx.mock:
            respx.put("http://test.com/api/resource/1").mock(
                return_value=httpx.Response(200, json={"status": "ok"})
            )

            await client.put(
                "http://test.com/api/resource/1",
                headers={"Content-Type": "application/json"},
            )

            assert (
                respx.calls.last.request.headers["Content-Type"] == "application/json"
            )

    @pytest.mark.asyncio
    async def test_put_raises_on_error(self, client):
        """Test put raises HTTPError on HTTP error."""
        with respx.mock:
            respx.put("http://test.com/api/resource/1").mock(
                return_value=httpx.Response(400)
            )

            with pytest.raises(httpx.HTTPStatusError):
                await client.put(
                    "http://test.com/api/resource/1", json={"name": "test"}
                )
