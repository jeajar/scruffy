from datetime import datetime

import httpx

from scruffy.infra.data_transfer_objects import MediaInfoDTO


class SonarrRepository:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.headers = {"X-Api-Key": api_key, "Accept": "application/json"}

    async def get_series(self, series_id: int) -> dict:
        """Get detailed information about a series by its Sonarr ID.

        Args:
            series_id: The Sonarr internal ID of the series

        Returns:
            Dict containing full series information

        Raises:
            httpx.HTTPError: If the API request fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v3/series/{series_id}", headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    async def get_series_info(
        self, series_id: int, season_list: list[int]
    ) -> MediaInfoDTO:
        """Get detailed information about a series by its Sonarr ID.

        Args:
            series_id: The Sonarr internal ID of the series

        Returns:
            Dict containing full series information

        Raises:
            httpx.HTTPError: If the API request fails
        """
        series = await self.get_series(series_id)
        available = True
        latest_date = None
        total_size = 0

        for season_num in season_list:
            episodes = await self.get_episodes(series_id, season_num)

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
            total_size += sum(ep.get("episodeFile", {}).get("size") for ep in episodes)

        return MediaInfoDTO(
            title=series.get("title"),
            available=available,
            available_since=latest_date if available else None,
            size_on_disk=total_size,
            seasons=season_list,
            id=series_id,
        )

    async def get_episodes(self, series_id: int, season_number: int) -> list[dict]:
        """Get episodes for a specific season of a series.

        Args:
            series_id: The Sonarr internal ID of the series
            season_number: The season number to fetch

        Returns:
            List of dictionaries containing episode information

        Raises:
            httpx.HTTPError: If the API request fails
        """
        async with httpx.AsyncClient() as client:
            params = {
                "seriesId": series_id,
                "seasonNumber": season_number,
                "includeEpisodeFile": True,
            }
            response = await client.get(
                f"{self.base_url}/api/v3/episode", headers=self.headers, params=params
            )
            response.raise_for_status()
            return response.json()

    async def delete_series(self, series_id: int, delete_files: bool = True) -> None:
        """Delete a series and optionally its files"""
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base_url}/api/v3/series/{series_id}",
                headers=self.headers,
                params={"deleteFiles": str(delete_files).lower()},
            )
            response.raise_for_status()

    async def delete_episode_files(self, episode_file_ids: list[int]) -> None:
        """Delete episode files by their Sonarr internal IDs"""
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base_url}/api/v3/episodeFile/bulk",
                headers=self.headers,
                json={"episodeFileIds": episode_file_ids},
            )
            response.raise_for_status()

    async def update_season_monitoring(
        self, series_id: int, seasons_to_unmonitor: list[int]
    ) -> None:
        """Update monitoring status for specific seasons of a series.

        Args:
            series_id: The Sonarr internal ID of the series
            seasons_to_unmonitor: List of season numbers to set as unmonitored

        Raises:
            httpx.HTTPError: If the API request fails
        """
        # Get current series config
        series = await self.get_series(series_id)

        # Update monitoring status for specified seasons
        for season in series["seasons"]:
            if season["seasonNumber"] in seasons_to_unmonitor:
                season["monitored"] = False

        # Update series via API
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.base_url}/api/v3/series/{series_id}",
                headers=self.headers,
                json=series,
            )
            response.raise_for_status()


if __name__ == "__main__":
    import asyncio
    import os

    # Load Sonarr API key from environment variable
    api_key = os.getenv("SONARR_API_KEY")
    base_url = "https://sonarr.jmax.tech"
    repo = SonarrRepository(base_url, api_key)
    series = asyncio.run(repo.get_episodes(12, 11))
    pass
