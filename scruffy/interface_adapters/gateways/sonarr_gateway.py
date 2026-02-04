"""Gateway adapter for Sonarr API (TV shows)."""

import asyncio
import logging
from datetime import datetime
from typing import TYPE_CHECKING

from scruffy.domain.value_objects.media_type import MediaType
from scruffy.frameworks_and_drivers.http.http_client import HttpClient
from scruffy.use_cases.dtos.media_info_dto import MediaInfoDTO
from scruffy.use_cases.interfaces.media_repository_interface import (
    MediaRepositoryInterface,
)

if TYPE_CHECKING:
    from scruffy.frameworks_and_drivers.database.settings_store import (
        SettingsProvider,
    )

logger = logging.getLogger(__name__)


class SonarrGateway(MediaRepositoryInterface):
    """Adapter for Sonarr API (TV shows)."""

    def __init__(
        self,
        settings_provider: "SettingsProvider",
        http_client: HttpClient | None = None,
    ):
        """Initialize Sonarr gateway with settings provider for runtime config."""
        self._settings_provider = settings_provider
        self.http_client = http_client or HttpClient()
        logger.debug("Initialized SonarrGateway")

    def _get_config(self) -> tuple[str, dict]:
        """Get base_url and headers from settings (DB + env fallback)."""
        config = self._settings_provider.get_services_config()
        base_url = config.sonarr_url.rstrip("/")
        api_key = config.sonarr_api_key or ""
        headers = {"X-Api-Key": api_key, "Accept": "application/json"}
        return base_url, headers

    async def status(self) -> bool:
        """Test Sonarr connection status."""
        base_url, headers = self._get_config()
        try:
            await self.http_client.get(
                f"{base_url}/api/v3/system/status", headers=headers
            )
            logger.info(
                "Sonarr connection successful", extra={"base_url": base_url}
            )
            return True
        except Exception as e:
            logger.warning(
                "Sonarr connection failed",
                extra={"base_url": base_url, "error": str(e)},
            )
            return False

    async def get_media(
        self, external_service_id: int, media_type: MediaType, seasons: list[int]
    ) -> MediaInfoDTO:
        """Get detailed information about a series by its Sonarr ID."""
        if media_type != MediaType.TV:
            raise ValueError("SonarrGateway only handles TV shows")

        base_url, headers = self._get_config()
        logger.debug(
            "Fetching series from Sonarr",
            extra={"external_service_id": external_service_id, "seasons": seasons},
        )

        series = await self.http_client.get(
            f"{base_url}/api/v3/series/{external_service_id}",
            headers=headers,
        )

        available = True
        latest_date = None
        total_size = 0
        poster = self._get_series_poster(series.get("images", []))
        title = series.get("title", "")

        episode_lists = await asyncio.gather(
            *[
                self.get_episodes(external_service_id, season_num)
                for season_num in seasons
            ]
        )

        for season_num, episodes in zip(seasons, episode_lists, strict=False):
            # Check if all episodes in season have files
            if not all(ep.get("hasFile", False) for ep in episodes):
                available = False
                logger.debug(
                    "Season not fully available",
                    extra={
                        "series_id": external_service_id,
                        "season": season_num,
                        "title": title,
                    },
                )
                break

            # Find latest episode file date
            season_dates = [
                datetime.fromisoformat(
                    ep["episodeFile"]["dateAdded"].replace("Z", "+00:00")
                )
                for ep in episodes
                if ep.get("episodeFile", {}).get("dateAdded")
            ]
            if season_dates:
                season_latest = max(season_dates)
                latest_date = (
                    max(latest_date, season_latest) if latest_date else season_latest
                )
            total_size += sum(
                ep.get("episodeFile", {}).get("size", 0) for ep in episodes
            )

        logger.info(
            "Retrieved series info",
            extra={
                "external_service_id": external_service_id,
                "title": title,
                "seasons": seasons,
                "available": available,
                "size_on_disk": total_size,
            },
        )

        return MediaInfoDTO(
            available_since=latest_date if available else None,
            available=available,
            id=external_service_id,
            poster=poster or "",
            seasons=seasons,
            size_on_disk=total_size,
            title=title,
        )

    async def delete_media(
        self, external_service_id: int, media_type: MediaType, seasons: list[int]
    ) -> None:
        """Delete specific seasons from a series and all their files."""
        if media_type != MediaType.TV:
            raise ValueError("SonarrGateway only handles TV shows")

        logger.info(
            "Deleting seasons from Sonarr",
            extra={"external_service_id": external_service_id, "seasons": seasons},
        )

        await self.update_season_monitoring(external_service_id, seasons)
        await self.delete_season_files(external_service_id, seasons)
        await self._delete_empty_series(external_service_id)

        logger.info(
            "Seasons deleted successfully",
            extra={"external_service_id": external_service_id, "seasons": seasons},
        )

    async def get_series(self, series_id: int) -> dict:
        """Get detailed information about a series by its Sonarr ID."""
        base_url, headers = self._get_config()
        return await self.http_client.get(
            f"{base_url}/api/v3/series/{series_id}", headers=headers
        )

    async def get_episodes(self, series_id: int, season_number: int) -> list[dict]:
        """Get episodes for a specific season of a series."""
        base_url, headers = self._get_config()
        logger.debug(
            "Fetching episodes",
            extra={"series_id": series_id, "season_number": season_number},
        )
        return await self.http_client.get(
            f"{base_url}/api/v3/episode",
            headers=headers,
            params={
                "seriesId": series_id,
                "seasonNumber": season_number,
                "includeEpisodeFile": True,
            },
        )

    async def delete_season_files(self, series_id: int, season_list: list[int]) -> None:
        """Delete specific seasons from a series and their files."""
        episode_file_ids = []
        for season in season_list:
            episode_data = await self.get_episodes(series_id, season)
            episode_file_ids.extend(
                [
                    ep.get("episodeFileId")
                    for ep in episode_data
                    if ep.get("episodeFileId")
                ]
            )

        # Delete episode files if any exist
        if episode_file_ids:
            logger.debug(
                "Deleting episode files",
                extra={"series_id": series_id, "file_count": len(episode_file_ids)},
            )
            await self.delete_episode_files(episode_file_ids)

    async def delete_episode_files(self, episode_file_ids: list[int]) -> None:
        """Delete episode files by their Sonarr internal IDs one at a time."""
        base_url, headers = self._get_config()
        for episode_id in episode_file_ids:
            await self.http_client.delete(
                f"{base_url}/api/v3/episodefile/{episode_id}",
                headers=headers,
            )

    async def update_season_monitoring(
        self, series_id: int, seasons_to_unmonitor: list[int]
    ) -> None:
        """Update monitoring status for specific seasons of a series."""
        base_url, headers = self._get_config()
        logger.debug(
            "Updating season monitoring",
            extra={
                "series_id": series_id,
                "seasons_to_unmonitor": seasons_to_unmonitor,
            },
        )
        series = await self.get_series(series_id)

        # Update monitoring status for specified seasons
        for season in series["seasons"]:
            if season["seasonNumber"] in seasons_to_unmonitor:
                season["monitored"] = False

        # Update series via API
        await self.http_client.put(
            f"{base_url}/api/v3/series/{series_id}",
            headers=headers,
            json=series,
        )

    async def _delete_empty_series(self, series_id: int) -> None:
        """Delete series if all seasons are unmonitored."""
        base_url, headers = self._get_config()
        series = await self.get_series(series_id)
        if all(not season["monitored"] for season in series["seasons"]):
            logger.info(
                "Deleting empty series (all seasons unmonitored)",
                extra={"series_id": series_id, "title": series.get("title")},
            )
            await self.http_client.delete(
                f"{base_url}/api/v3/series/{series_id}",
                headers=headers,
                params={"deleteFiles": False, "addImportListExclusion": False},
            )

    @staticmethod
    def _get_series_poster(images: list[dict]) -> str | None:
        """Get poster URL from images."""
        poster = next(
            (img["remoteUrl"] for img in images if img.get("coverType") == "poster"),
            None,
        )
        return poster
