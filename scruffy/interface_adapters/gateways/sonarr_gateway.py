from datetime import datetime

from scruffy.domain.value_objects.media_type import MediaType
from scruffy.frameworks_and_drivers.http.http_client import HttpClient
from scruffy.use_cases.dtos.media_info_dto import MediaInfoDTO
from scruffy.use_cases.interfaces.media_repository_interface import (
    MediaRepositoryInterface,
)


class SonarrGateway(MediaRepositoryInterface):
    """Adapter for Sonarr API (TV shows)."""

    def __init__(self, base_url: str, api_key: str, http_client: HttpClient | None = None):
        """Initialize Sonarr gateway."""
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.headers = {"X-Api-Key": api_key, "Accept": "application/json"}
        self.http_client = http_client or HttpClient()

    async def get_media(
        self, external_service_id: int, media_type: MediaType, seasons: list[int]
    ) -> MediaInfoDTO:
        """Get detailed information about a series by its Sonarr ID."""
        if media_type != MediaType.TV:
            raise ValueError("SonarrGateway only handles TV shows")

        series = await self.http_client.get(
            f"{self.base_url}/api/v3/series/{external_service_id}",
            headers=self.headers,
        )

        available = True
        latest_date = None
        total_size = 0
        poster = self._get_series_poster(series.get("images", []))

        for season_num in seasons:
            episodes = await self.get_episodes(external_service_id, season_num)

            # Check if all episodes in season have files
            if not all(ep.get("hasFile", False) for ep in episodes):
                available = False
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

        return MediaInfoDTO(
            available_since=latest_date if available else None,
            available=available,
            id=external_service_id,
            poster=poster or "",
            seasons=seasons,
            size_on_disk=total_size,
            title=series.get("title", ""),
        )

    async def delete_media(
        self, external_service_id: int, media_type: MediaType, seasons: list[int]
    ) -> None:
        """Delete specific seasons from a series and all their files."""
        if media_type != MediaType.TV:
            raise ValueError("SonarrGateway only handles TV shows")

        await self.update_season_monitoring(external_service_id, seasons)
        await self.delete_season_files(external_service_id, seasons)
        await self._delete_empty_series(external_service_id)

    async def get_series(self, series_id: int) -> dict:
        """Get detailed information about a series by its Sonarr ID."""
        return await self.http_client.get(
            f"{self.base_url}/api/v3/series/{series_id}", headers=self.headers
        )

    async def get_episodes(self, series_id: int, season_number: int) -> list[dict]:
        """Get episodes for a specific season of a series."""
        return await self.http_client.get(
            f"{self.base_url}/api/v3/episode",
            headers=self.headers,
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
            await self.delete_episode_files(episode_file_ids)

    async def delete_episode_files(self, episode_file_ids: list[int]) -> None:
        """Delete episode files by their Sonarr internal IDs one at a time."""
        for episode_id in episode_file_ids:
            await self.http_client.delete(
                f"{self.base_url}/api/v3/episodefile/{episode_id}",
                headers=self.headers,
            )

    async def update_season_monitoring(
        self, series_id: int, seasons_to_unmonitor: list[int]
    ) -> None:
        """Update monitoring status for specific seasons of a series."""
        series = await self.get_series(series_id)

        # Update monitoring status for specified seasons
        for season in series["seasons"]:
            if season["seasonNumber"] in seasons_to_unmonitor:
                season["monitored"] = False

        # Update series via API
        await self.http_client.put(
            f"{self.base_url}/api/v3/series/{series_id}",
            headers=self.headers,
            json=series,
        )

    async def _delete_empty_series(self, series_id: int) -> None:
        """Delete series if all seasons are unmonitored."""
        series = await self.get_series(series_id)
        if all(not season["monitored"] for season in series["seasons"]):
            await self.http_client.delete(
                f"{self.base_url}/api/v3/series/{series_id}",
                headers=self.headers,
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
