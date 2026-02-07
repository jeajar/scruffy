"""End-to-end integration tests for complete workflows."""

import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest
import respx

from scruffy.domain.entities.media import Media
from scruffy.domain.entities.media_request import MediaRequest
from scruffy.frameworks_and_drivers.config.settings import settings as app_settings
from scruffy.frameworks_and_drivers.database.settings_store import (
    ServicesConfig,
    invalidate_services_config_cache,
)
from scruffy.frameworks_and_drivers.di.container import Container

# Test URLs used by respx mocks; must match mock_settings patches
OVERSEERR_BASE = "http://overseerr.test"
RADARR_BASE = "http://radarr.test"
SONARR_BASE = "http://sonarr.test"


@pytest.fixture
def _mock_settings():
    """Mock settings for integration tests.

    Patches the real config.settings object so SettingsProvider and any
    code using it (via settings_store or config) see test URLs.
    """
    mock_values = {
        "overseerr_url": OVERSEERR_BASE,
        "overseerr_api_key": "overseerr-key",
        "sonarr_url": SONARR_BASE,
        "sonarr_api_key": "sonarr-key",
        "radarr_url": RADARR_BASE,
        "radarr_api_key": "radarr-key",
        "retention_days": 30,
        "reminder_days": 7,
        "email_enabled": False,
    }
    invalidate_services_config_cache()
    patches = [patch.object(app_settings, k, v) for k, v in mock_values.items()]
    with patch(
        "scruffy.frameworks_and_drivers.database.settings_store.settings",
        app_settings,
    ):
        for p in patches:
            p.start()
        try:
            yield app_settings
        finally:
            for p in reversed(patches):
                p.stop()


@pytest.fixture
def in_memory_engine():
    """Database engine for integration tests.

    Uses a temp file (not :memory:) so connections from the thread pool
    (asyncio.to_thread) see the same database as the main thread.
    """
    from sqlalchemy import create_engine
    from sqlmodel import SQLModel

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        engine = create_engine(f"sqlite:///{db_path}")
        SQLModel.metadata.create_all(engine)
        yield engine
    finally:
        SQLModel.metadata.drop_all(engine)
        Path(db_path).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_complete_workflow_check_remind_delete(_mock_settings, in_memory_engine):
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

            # Patch get_engine at source so Container and SettingsProvider use test DB
            invalidate_services_config_cache()
            test_config = ServicesConfig()
            test_config.overseerr_url = overseerr_base
            test_config.overseerr_api_key = "overseerr-key"
            test_config.radarr_url = radarr_base
            test_config.radarr_api_key = "radarr-key"
            test_config.sonarr_url = SONARR_BASE
            test_config.sonarr_api_key = "sonarr-key"
            with (
                patch(
                    "scruffy.frameworks_and_drivers.database.database.get_engine",
                    return_value=in_memory_engine,
                ),
                patch(
                    "scruffy.frameworks_and_drivers.database.settings_store._services_config_cache",
                    test_config,
                ),
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
async def test_complete_workflow_remind_only(_mock_settings, in_memory_engine):
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

            invalidate_services_config_cache()
            test_config = ServicesConfig()
            test_config.overseerr_url = overseerr_base
            test_config.overseerr_api_key = "overseerr-key"
            test_config.radarr_url = radarr_base
            test_config.radarr_api_key = "radarr-key"
            test_config.sonarr_url = SONARR_BASE
            test_config.sonarr_api_key = "sonarr-key"
            with (
                patch(
                    "scruffy.frameworks_and_drivers.database.database.get_engine",
                    return_value=in_memory_engine,
                ),
                patch(
                    "scruffy.frameworks_and_drivers.database.settings_store._services_config_cache",
                    test_config,
                ),
            ):
                container = Container()

                # Execute process use case (should remind, not delete)
                await container.process_media_use_case.execute()

            # Verify no delete was called
            delete_calls = [
                call for call in radarr_mock.calls if call.request.method == "DELETE"
            ]
            assert len(delete_calls) == 0

            # Verify reminder was added
            assert container._reminder_gateway.has_reminder(request_id=1) is True
