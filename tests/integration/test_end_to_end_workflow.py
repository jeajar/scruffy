"""End-to-end integration tests for complete workflows."""

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import httpx
import pytest
import respx

from scruffy.domain.entities.media import Media
from scruffy.domain.entities.media_request import MediaRequest
from scruffy.frameworks_and_drivers.di.container import Container


@pytest.fixture
def mock_settings():
    """Mock settings for integration tests."""
    with patch("scruffy.frameworks_and_drivers.di.container.settings") as mock:
        mock.overseerr_url = "http://overseerr.test"
        mock.overseerr_api_key = "overseerr-key"
        mock.sonarr_url = "http://sonarr.test"
        mock.sonarr_api_key = "sonarr-key"
        mock.radarr_url = "http://radarr.test"
        mock.radarr_api_key = "radarr-key"
        mock.retention_days = 30
        mock.reminder_days = 7
        mock.email_enabled = False  # Disable email for integration tests
        yield mock


@pytest.fixture
def in_memory_engine():
    """In-memory database engine for integration tests."""
    from sqlalchemy import create_engine
    from sqlmodel import SQLModel

    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_complete_workflow_check_remind_delete(mock_settings, in_memory_engine):
    """Test complete workflow: check → remind → delete."""
    # Mock Overseerr API
    overseerr_base = "http://overseerr.test"
    with respx.mock(base_url=overseerr_base) as respx_mock:
        # Count is not called when first page has pageInfo.total
        # Mock get requests
        respx_mock.get("/api/v1/request").mock(
            return_value=httpx.Response(
                200,
                json={
                    "pageInfo": {"pages": 1, "pageSize": 10, "results": 1, "total": 1},
                    "results": [
                        {
                            "id": 1,
                            "type": "movie",
                            "status": "approved",
                            "requestedBy": {"id": 1, "email": "test@example.com"},
                            "media": {
                                "status": "available",
                                "externalServiceId": 100,
                                "updatedAt": (
                                    datetime.now(UTC) - timedelta(days=31)
                                ).isoformat(),
                                "id": 99,
                            },
                        }
                    ],
                },
            )
        )
        # Mock delete request
        respx_mock.delete("/api/v1/request/1").mock(return_value=httpx.Response(200))
        # Mock delete media
        respx_mock.delete("/api/v1/media/99").mock(return_value=httpx.Response(200))

        # Mock Radarr API
        radarr_base = "http://radarr.test"
        with respx.mock(base_url=radarr_base) as radarr_mock:
            radarr_mock.get("/api/v3/movie/100").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "id": 100,
                        "title": "Test Movie",
                        "hasFile": True,
                        "sizeOnDisk": 1000000,
                        "images": [
                            {
                                "coverType": "poster",
                                "remoteUrl": "http://test.com/poster.jpg",
                            }
                        ],
                        "movieFile": {
                            "dateAdded": (
                                datetime.now(UTC) - timedelta(days=31)
                            ).isoformat()
                        },
                    },
                )
            )
            radarr_mock.delete("/api/v3/movie/100").mock(
                return_value=httpx.Response(200)
            )

            # Patch database engine
            with patch(
                "scruffy.frameworks_and_drivers.di.container.get_engine",
                return_value=in_memory_engine,
            ):
                container = Container()

                # Execute check use case
                results = await container.check_media_requests_use_case.execute()

                assert len(results) == 1
                request, media = results[0]
                assert isinstance(request, MediaRequest)
                assert isinstance(media, Media)
                assert request.request_id == 1
                assert media.title == "Test Movie"

                # Execute process use case (should delete since past retention)
                await container.process_media_use_case.execute()

                # Verify delete was called
                assert any(
                    call.request.url.path == "/api/v3/movie/100"
                    for call in radarr_mock.calls
                    if call.request.method == "DELETE"
                )
                assert any(
                    call.request.url.path == "/api/v1/request/1"
                    for call in respx_mock.calls
                    if call.request.method == "DELETE"
                )


@pytest.mark.asyncio
async def test_complete_workflow_remind_only(mock_settings, in_memory_engine):
    """Test complete workflow: check → remind (no delete)."""
    # Mock Overseerr API
    overseerr_base = "http://overseerr.test"
    with respx.mock(base_url=overseerr_base) as respx_mock:
        # Count is not called when first page has pageInfo.total
        respx_mock.get("/api/v1/request").mock(
            return_value=httpx.Response(
                200,
                json={
                    "pageInfo": {"pages": 1, "pageSize": 10, "results": 1, "total": 1},
                    "results": [
                        {
                            "id": 1,
                            "type": "movie",
                            "status": "approved",
                            "requestedBy": {"id": 1, "email": "test@example.com"},
                            "media": {
                                "status": "available",
                                "externalServiceId": 100,
                                "updatedAt": (
                                    datetime.now(UTC) - timedelta(days=24)
                                ).isoformat(),
                                "id": 99,
                            },
                        }
                    ],
                },
            )
        )

        # Mock Radarr API
        radarr_base = "http://radarr.test"
        with respx.mock(base_url=radarr_base) as radarr_mock:
            radarr_mock.get("/api/v3/movie/100").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "id": 100,
                        "title": "Test Movie",
                        "hasFile": True,
                        "sizeOnDisk": 1000000,
                        "images": [],
                        "movieFile": {
                            "dateAdded": (
                                datetime.now(UTC) - timedelta(days=24)
                            ).isoformat()
                        },
                    },
                )
            )

            with patch(
                "scruffy.frameworks_and_drivers.di.container.get_engine",
                return_value=in_memory_engine,
            ):
                container = Container()

                # Execute process use case (should remind, not delete)
                await container.process_media_use_case.execute()

                # Verify no delete was called
                delete_calls = [
                    call
                    for call in radarr_mock.calls
                    if call.request.method == "DELETE"
                ]
                assert len(delete_calls) == 0

                # Verify reminder was added
                assert container._reminder_gateway.has_reminder(request_id=1) is True
