"""Gateway adapter for Radarr API (movies)."""

import logging
from datetime import datetime
from typing import TYPE_CHECKING

from scruffy.domain.value_objects.media_type import MediaType
from scruffy.interface_adapters.interfaces.http_client_interface import (
    HttpClientInterface,
)
from scruffy.use_cases.dtos.media_info_dto import MediaInfoDTO
from scruffy.use_cases.interfaces.media_repository_interface import (
    MediaRepositoryInterface,
)

if TYPE_CHECKING:
    from scruffy.frameworks_and_drivers.database.settings_store import (
        SettingsProvider,
    )

logger = logging.getLogger(__name__)


class RadarrGateway(MediaRepositoryInterface):
    """Adapter for Radarr API (movies)."""

    def __init__(
        self,
        settings_provider: "SettingsProvider",
        http_client: HttpClientInterface,
    ):
        """Initialize Radarr gateway with settings provider for runtime config."""
        self._settings_provider = settings_provider
        self.http_client = http_client
        logger.debug("Initialized RadarrGateway")

    def _get_config(self) -> tuple[str, dict]:
        """Get base_url and headers from settings (DB + env fallback)."""
        config = self._settings_provider.get_services_config()
        base_url = config.radarr_url.rstrip("/")
        api_key = config.radarr_api_key or ""
        headers = {"X-Api-Key": api_key, "Accept": "application/json"}
        return base_url, headers

    async def status(self) -> bool:
        """Test Radarr connection status."""
        base_url, headers = self._get_config()
        try:
            await self.http_client.get(
                f"{base_url}/api/v3/system/status", headers=headers
            )
            logger.info("Radarr connection successful", extra={"base_url": base_url})
            return True
        except Exception as e:
            logger.warning(
                "Radarr connection failed",
                extra={"base_url": base_url, "error": str(e)},
            )
            return False

    async def get_media(
        self, external_service_id: int, media_type: MediaType, seasons: list[int]
    ) -> MediaInfoDTO:
        """Get detailed information about a movie by its Radarr ID."""
        if media_type != MediaType.MOVIE:
            raise ValueError("RadarrGateway only handles movies")

        base_url, headers = self._get_config()
        logger.debug(
            "Fetching movie from Radarr",
            extra={"external_service_id": external_service_id},
        )

        data = await self.http_client.get(
            f"{base_url}/api/v3/movie/{external_service_id}",
            headers=headers,
        )

        poster = self._get_movie_poster(data.get("images", []))
        added_at = data.get("movieFile", {}).get("dateAdded")
        title = data.get("title")

        logger.info(
            "Retrieved movie info",
            extra={
                "external_service_id": external_service_id,
                "title": title,
                "has_file": data.get("hasFile"),
                "size_on_disk": data.get("sizeOnDisk", 0),
            },
        )

        return MediaInfoDTO(
            title=title,
            available=data.get("hasFile"),
            poster=poster or "",
            available_since=datetime.fromisoformat(added_at) if added_at else None,
            size_on_disk=data.get("sizeOnDisk", 0),
            id=data.get("id"),
            seasons=[],
        )

    async def delete_media(
        self, external_service_id: int, media_type: MediaType, seasons: list[int]
    ) -> None:
        """Delete a movie and optionally its files."""
        if media_type != MediaType.MOVIE:
            raise ValueError("RadarrGateway only handles movies")

        base_url, headers = self._get_config()
        logger.info(
            "Deleting movie from Radarr",
            extra={"external_service_id": external_service_id},
        )

        await self.http_client.delete(
            f"{base_url}/api/v3/movie/{external_service_id}",
            headers=headers,
            params={"deleteFiles": "true"},
        )

        logger.info(
            "Movie deleted successfully",
            extra={"external_service_id": external_service_id},
        )

    def _get_movie_poster(self, images: list[dict]) -> str | None:
        """Get poster URL from images."""
        poster = next(
            (img["remoteUrl"] for img in images if img.get("coverType") == "poster"),
            None,
        )
        return poster
