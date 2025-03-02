from datetime import datetime

import httpx

from scruffy.infra.data_transfer_objects import MediaInfoDTO


class RadarrRepository:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.headers = {"X-Api-Key": api_key, "Accept": "application/json"}

    async def status(self) -> bool:
        """
        Test Radarr connection status.
        Returns True if the connection is successful, False otherwise.
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v3/system/status", headers=self.headers
                )
                response.raise_for_status()
                return True
        except httpx.HTTPError:
            return False

    def _get_movie_poster(self, images: list[dict]) -> str:
        # Get poster URL from images
        poster = next(
            (img["remoteUrl"] for img in images if img.get("coverType") == "poster"),
            None,
        )
        return poster

    async def get_movie(self, movie_id: int) -> MediaInfoDTO:
        """Get detailed information about a movie by its Radarr ID.

        Args:
            movie_id: The Radarr internal ID of the movie

        Returns:
            Dict containing full movie information

        Raises:
            httpx.HTTPError: If the API request fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v3/movie/{movie_id}", headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            poster = self._get_movie_poster(data.get("images", []))
            added_at = data.get("movieFile", {}).get("dateAdded")
            return MediaInfoDTO(
                title=data.get("title"),
                available=data.get("hasFile"),
                poster=poster,
                available_since=datetime.fromisoformat(added_at) if added_at else None,
                size_on_disk=data.get("sizeOnDisk"),
                id=data.get("id"),
                seasons=[],
            )

    async def delete_movie(self, movie_id: int, delete_files: bool = True) -> None:
        """Delete a movie and optionally its files.

        Args:
            movie_id: The Radarr internal ID of the movie
            delete_files: Whether to delete the associated movie files

        Raises:
            httpx.HTTPError: If the API request fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base_url}/api/v3/movie/{movie_id}",
                headers=self.headers,
                params={"deleteFiles": str(delete_files).lower()},
            )
            response.raise_for_status()
