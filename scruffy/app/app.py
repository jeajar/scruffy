import asyncio
from datetime import datetime

from rich import print

from scruffy.infra import (
    MediaStatus,
    OverseerRepository,
    RadarrRepository,
    SonarrRepository,
    settings,
)


def main():
    overseer = OverseerRepository(str(settings.OVERSEER_URL), settings.OVERSEER_API_KEY)
    sonarr = SonarrRepository(str(settings.SONARR_URL), settings.SONARR_API_KEY)
    radarr = RadarrRepository(str(settings.RADARR_URL), settings.RADARR_API_KEY)

    # Get all requests from Overseerr
    requests = asyncio.run(overseer.get_requests())

    # Check only requests that are partially or fully available. Overseer is reporting
    # tv request as PARTIALLY_AVAILABLE when not all seasons are requested.
    to_check = [
        req
        for req in requests
        if req.media_status in [MediaStatus.PARTIALLY_AVAILABLE, MediaStatus.AVAILABLE]
    ]

    tv_requests = [req for req in to_check if req.type == "tv"]
    movie_requests = [req for req in to_check if req.type == "movie"]

    # Check TV requests
    for req in tv_requests:
        series_info = asyncio.run(
            sonarr.get_series_info(req.external_service_id, req.seasons)
        )
        if series_info.available:
            age = (
                datetime.now(series_info.available_since.tzinfo)
                - series_info.available_since
            )
            print(
                f"{len(req.seasons)} requested seasons of '{series_info.title}' have been [green]available[/green] for {age.days} days."
            )
        else:
            print(
                f"{len(req.seasons)} requested seasons of '{series_info.title}' are [red]not available[/red] yet."
            )
        # print(series_info)

    # Check movie requests
    for req in movie_requests:
        movie_info = asyncio.run(radarr.get_movie(req.external_service_id))
        if movie_info.available:
            age = (
                datetime.now(movie_info.available_since.tzinfo)
                - movie_info.available_since
            )
            print(
                f"'{movie_info.title}' has been [green]available[/green] for {age.days} days."
            )
        else:
            print(f"'{movie_info.title}' is [red]not available[/red] yet")

    pass


if __name__ == "__main__":
    main()
