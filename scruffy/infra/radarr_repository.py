import httpx

from scruffy.infra.data_transfer_objects import MediaInfoDTO


class RadarrRepository:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.headers = {"X-Api-Key": api_key, "Accept": "application/json"}

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
            return MediaInfoDTO.from_radarr_response(response.json())

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


if __name__ == "__main__":
    import asyncio
    import os

    api_key = os.getenv("RADARR_API_KEY")
    base_url = "https://radarr.jmax.tech"
    repo = RadarrRepository(base_url, api_key)
    movie = asyncio.run(repo.get_movie(58))
    movie_info_dto = MediaInfoDTO.from_radarr_response(movie)
    pass
