"""Tests for mapper functions."""



from scruffy.domain.entities.media import Media
from scruffy.domain.entities.media_request import MediaRequest
from scruffy.domain.value_objects.media_type import MediaType
from scruffy.use_cases.dtos.media_info_dto import MediaInfoDTO
from scruffy.use_cases.mappers import (
    map_media_dto_to_entity,
    map_media_entity_to_dto,
    map_request_dto_to_entity,
)


def test_map_media_dto_to_entity(sample_media_info_dto):
    """Test mapping MediaInfoDTO to Media entity."""
    entity = map_media_dto_to_entity(sample_media_info_dto)

    assert isinstance(entity, Media)
    assert entity.id == sample_media_info_dto.id
    assert entity.title == sample_media_info_dto.title
    assert entity.available == sample_media_info_dto.available
    assert entity.available_since == sample_media_info_dto.available_since
    assert entity.size_on_disk == sample_media_info_dto.size_on_disk
    assert entity.poster == sample_media_info_dto.poster
    assert entity.seasons == sample_media_info_dto.seasons


def test_map_media_entity_to_dto(sample_media_entity):
    """Test mapping Media entity to MediaInfoDTO."""
    dto = map_media_entity_to_dto(sample_media_entity)

    assert isinstance(dto, MediaInfoDTO)
    assert dto.id == sample_media_entity.id
    assert dto.title == sample_media_entity.title
    assert dto.available == sample_media_entity.available
    assert dto.available_since == sample_media_entity.available_since
    assert dto.size_on_disk == sample_media_entity.size_on_disk
    assert dto.poster == sample_media_entity.poster
    assert dto.seasons == sample_media_entity.seasons


def test_map_request_dto_to_entity_movie(sample_request_dto_movie):
    """Test mapping RequestDTO to MediaRequest entity for movie."""
    entity = map_request_dto_to_entity(sample_request_dto_movie)

    assert isinstance(entity, MediaRequest)
    assert entity.user_id == sample_request_dto_movie.user_id
    assert entity.user_email == sample_request_dto_movie.user_email
    assert entity.media_type == MediaType.MOVIE
    assert entity.request_id == sample_request_dto_movie.request_id
    assert entity.request_status == sample_request_dto_movie.request_status
    assert entity.updated_at == sample_request_dto_movie.updated_at
    assert entity.media_id == sample_request_dto_movie.media_id
    assert entity.media_status == sample_request_dto_movie.media_status
    assert entity.external_service_id == sample_request_dto_movie.external_service_id
    assert entity.seasons == sample_request_dto_movie.seasons


def test_map_request_dto_to_entity_tv(sample_request_dto_tv):
    """Test mapping RequestDTO to MediaRequest entity for TV."""
    entity = map_request_dto_to_entity(sample_request_dto_tv)

    assert isinstance(entity, MediaRequest)
    assert entity.media_type == MediaType.TV
    assert entity.seasons == sample_request_dto_tv.seasons


def test_map_media_dto_to_entity_with_none_available_since():
    """Test mapping MediaInfoDTO with None available_since."""
    dto = MediaInfoDTO(
        id=1,
        title="Test",
        available=False,
        available_since=None,
        size_on_disk=0,
        poster="",
        seasons=[],
    )

    entity = map_media_dto_to_entity(dto)

    assert entity.available_since is None
    assert entity.available is False


def test_map_media_entity_to_dto_with_none_available_since():
    """Test mapping Media entity with None available_since."""
    entity = Media(
        id=1,
        title="Test",
        available=False,
        available_since=None,
        size_on_disk=0,
        poster="",
        seasons=[],
    )

    dto = map_media_entity_to_dto(entity)

    assert dto.available_since is None
    assert dto.available is False


def test_map_request_dto_to_entity_preserves_all_fields(sample_request_dto_movie):
    """Test mapping preserves all fields correctly."""
    entity = map_request_dto_to_entity(sample_request_dto_movie)

    # Verify all fields are mapped
    assert entity.user_id == sample_request_dto_movie.user_id
    assert entity.user_email == sample_request_dto_movie.user_email
    assert entity.request_id == sample_request_dto_movie.request_id
    assert entity.media_id == sample_request_dto_movie.media_id
    assert entity.external_service_id == sample_request_dto_movie.external_service_id
