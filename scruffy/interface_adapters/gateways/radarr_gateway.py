"""Gateway adapter for Radarr API (movies)."""

import logging
from datetime import datetime

from scruffy.domain.value_objects.media_type import MediaType
from scruffy.frameworks_and_drivers.http.http_client import HttpClient
from scruffy.use_cases.dtos.media_info_dto import MediaInfoDTO
from scruffy.use_cases.interfaces.media_repository_interface import (
    MediaRepositoryInterface,
)

logger = logging.getLogger(__name__)


class RadarrGateway(MediaRepositoryInterface):
    """Adapter for Radarr API (movies)."""

    def __init__(self, base_url: str, api_key: str, http_client: HttpClient | None = None):
        """Initialize Radarr gateway."""
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.headers = {"X-Api-Key": api_key, "Accept": "application/json"}
        self.http_client = http_client or HttpClient()
        logger.debug("Initialized RadarrGateway", extra={"base_url": self.base_url})

    async def status(self) -> bool:
        """Test Radarr connection status."""
        try:
            await self.http_client.get(
                f"{self.base_url}/api/v3/system/status", headers=self.headers
            )
            logger.info("Radarr connection successful", extra={"base_url": self.base_url})
            return True
        except Exception as e:
            logger.warning(
                "Radarr connection failed",
                extra={"base_url": self.base_url, "error": str(e)},
            )
            return False

    async def get_media(
        self, external_service_id: int, media_type: MediaType, seasons: list[int]
    ) -> MediaInfoDTO:
        """Get detailed information about a movie by its Radarr ID."""
        if media_type != MediaType.MOVIE:
            raise ValueError("RadarrGateway only handles movies")

        logger.debug(
            "Fetching movie from Radarr",
            extra={"external_service_id": external_service_id},
        )

        data = await self.http_client.get(
            f"{self.base_url}/api/v3/movie/{external_service_id}",
            headers=self.headers,
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

        logger.info(
            "Deleting movie from Radarr",
            extra={"external_service_id": external_service_id},
        )

        await self.http_client.delete(
            f"{self.base_url}/api/v3/movie/{external_service_id}",
            headers=self.headers,
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
