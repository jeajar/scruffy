import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Union

from scruffy.infra import (
    MediaInfoDTO,
    MediaStatus,
    OverseerRepository,
    RadarrRepository,
    RequestDTO,
    SonarrRepository,
    settings,
)
from scruffy.services import EmailService


@dataclass(frozen=True)
class Result:
    requests_to_delete: list[RequestDTO]
    delete_to_notify: list[MediaInfoDTO]
    reminders: list[MediaInfoDTO]


def check_requests() -> dict[int : dict[str, Union[RequestDTO, MediaInfoDTO]]]:
    """
    Check each request from Overseerr and get the media information from Sonarr or Radarr.
    The returned data can be used to apply the retention policy and/or send
    notifications to the user.

    Returns:
        A dictionary with the request_id and the request and media information.
    """
    overseer = OverseerRepository(
        str(settings.OVERSEERR_URL), settings.OVERSEERR_API_KEY
    )
    sonarr = SonarrRepository(str(settings.SONARR_URL), settings.SONARR_API_KEY)
    radarr = RadarrRepository(str(settings.RADARR_URL), settings.RADARR_API_KEY)

    # Get all requests from Overseerr
    requests = asyncio.run(overseer.get_requests())

    # Note: Overseerr always reports tv requests as "partially available"
    # when not all seasons were requested. We need to check in Sonarr for the full availability
    # information.
    to_check = [
        req
        for req in requests
        if req.media_status in [MediaStatus.PARTIALLY_AVAILABLE, MediaStatus.AVAILABLE]
    ]

    result = {}
    # Check Requests with available media for age.
    for req in to_check:
        if req.type == "movie":
            media_info = asyncio.run(radarr.get_movie(req.external_service_id))
        elif req.type == "tv":
            media_info = asyncio.run(
                sonarr.get_series_info(req.external_service_id, req.seasons)
            )
        result[req.request_id] = {"request": req, "media_info": media_info}

    return result


def apply_retention_policy(requests: dict[RequestDTO, MediaInfoDTO]) -> Result:
    # List of requests that have expired and need to be deleted on disk
    requests_to_delete: list[RequestDTO] = []

    # List of media that will be deleted on disk to notify the user
    delete_to_notify: list[MediaInfoDTO] = []

    # List of media that will expire soon and need to notify the user
    reminders: list[MediaInfoDTO] = []
    for req, media_info in requests.items():
        if media_info.available:
            age = datetime.now(media_info.available_since.tzinfo) - req.updated_at
            if age.days >= settings.RETENTION_DAYS:
                requests_to_delete.append(req)
                delete_to_notify.append(media_info)

            # Add to reminders if the request is about to expire so we can notify the user.
            if settings.RETENTION_DAYS - age.days == settings.REMINDER_DAYS:
                reminders.append(media_info)

    return Result(
        requests_to_delete=requests_to_delete,
        delete_to_notify=delete_to_notify,
        reminders=reminders,
    )


if __name__ == "__main__":
    dev_mail = EmailService()
    result = check_requests()

    for req_it, data in result.items():
        asyncio.run(
            dev_mail.send_reminder_notice("user@example.com", data.get("media_info"), 5)
        )
        asyncio.run(
            dev_mail.send_deletion_notice("user@example.com", data.get("media_info"))
        )
        # print(data.get("media_info"))
