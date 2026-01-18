"""Mappers to convert between DTOs and domain entities."""

from scruffy.domain.entities.media import Media
from scruffy.domain.entities.media_request import MediaRequest
from scruffy.use_cases.dtos.media_info_dto import MediaInfoDTO
from scruffy.use_cases.dtos.request_dto import RequestDTO


def map_media_dto_to_entity(dto: MediaInfoDTO) -> Media:
    """Convert MediaInfoDTO to Media domain entity."""
    return Media(
        id=dto.id,
        title=dto.title,
        available=dto.available,
        available_since=dto.available_since,
        size_on_disk=dto.size_on_disk,
        poster=dto.poster,
        seasons=dto.seasons,
    )


def map_media_entity_to_dto(entity: Media) -> MediaInfoDTO:
    """Convert Media domain entity to MediaInfoDTO."""
    return MediaInfoDTO(
        id=entity.id,
        title=entity.title,
        available=entity.available,
        available_since=entity.available_since,
        size_on_disk=entity.size_on_disk,
        poster=entity.poster,
        seasons=entity.seasons,
    )


def map_request_dto_to_entity(dto: RequestDTO) -> MediaRequest:
    """Convert RequestDTO to MediaRequest domain entity."""
    from scruffy.domain.value_objects.media_type import MediaType

    media_type = MediaType.MOVIE if dto.type == "movie" else MediaType.TV
    return MediaRequest(
        user_id=dto.user_id,
        user_email=dto.user_email,
        media_type=media_type,
        request_id=dto.request_id,
        request_status=dto.request_status,
        updated_at=dto.updated_at,
        media_id=dto.media_id,
        media_status=dto.media_status,
        external_service_id=dto.external_service_id,
        seasons=dto.seasons,
    )
