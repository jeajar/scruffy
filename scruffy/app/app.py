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
    requests_to_delete = []
    reminders = []

    # Check only requests that are partially or fully available. Overseer is reporting
    # tv request as PARTIALLY_AVAILABLE when not all seasons are requested.
    # We then need to check if the media is available for the requested seasons within
    # Sonarr.
    to_check = [
        req
        for req in requests
        if req.media_status in [MediaStatus.PARTIALLY_AVAILABLE, MediaStatus.AVAILABLE]
    ]

    # Check Requests with available media for age.
    for req in to_check:
        if req.type == "movie":
            media_info = asyncio.run(radarr.get_movie(req.external_service_id))
        elif req.type == "tv":
            media_info = asyncio.run(
                sonarr.get_series_info(req.external_service_id, req.seasons)
            )
        if media_info.available:
            age = datetime.now(media_info.available_since.tzinfo) - req.updated_at
            if age.days >= settings.RETENTION_DAYS:
                requests_to_delete.append(req)
            # Add to reminders if the request is about to expire so we can notify the user.
            if settings.RETENTION_DAYS - age.days == settings.REMINDER_DAYS:
                reminders.append(media_info)

    print(reminders)
    pass


if __name__ == "__main__":
    main()
