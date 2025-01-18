from datetime import datetime

from scruffy.infra.constants import MediaStatus, RequestStatus
from scruffy.infra.data_transfer_objects import MediaInfoDTO, RequestDTO


def test_request_dto_creation():
    request = RequestDTO(
        user_id=1,
        user_email="test@example.com",
        type="movie",
        request_id=100,
        request_status=RequestStatus.PENDING_APPROVAL,
        updated_at=datetime(2023, 1, 1),
        media_status=MediaStatus.AVAILABLE,
        external_service_id=1000,
        seasons=[],
    )

    assert request.user_id == 1
    assert request.user_email == "test@example.com"
    assert request.type == "movie"
    assert request.request_id == 100
    assert request.request_status == RequestStatus.PENDING_APPROVAL
    assert request.media_status == MediaStatus.AVAILABLE
    assert request.external_service_id == 1000
    assert request.seasons == []


def test_request_dto_from_overseer_movie_response():
    response = {
        "requestedBy": {"id": 1, "email": "test@example.com"},
        "type": "movie",
        "id": 100,
        "status": 1,
        "media": {
            "status": 1,
            "externalServiceId": 1000,
            "updatedAt": "2023-01-01T12:00:00",
        },
    }

    request = RequestDTO.from_overseer_response(response)
    assert request.user_id == 1
    assert request.type == "movie"
    assert request.seasons == []
    assert request.updated_at == datetime(2023, 1, 1, 12, 0, 0)


def test_request_dto_from_overseer_tv_response():
    response = {
        "requestedBy": {"id": 2, "email": "tv@example.com"},
        "type": "tv",
        "id": 200,
        "status": 1,
        "media": {
            "status": 3,
            "externalServiceId": 2000,
            "updatedAt": "2023-02-01T12:00:00",
        },
        "seasons": [{"seasonNumber": 1}, {"seasonNumber": 2}],
    }

    request = RequestDTO.from_overseer_response(response)
    assert request.user_id == 2
    assert request.type == "tv"
    assert request.seasons == [1, 2]
    assert request.media_status == MediaStatus.PROCESSING


def test_media_info_dto_creation():
    media = MediaInfoDTO(
        available_since=datetime(2023, 1, 1),
        available=True,
        id=100,
        poster="http://example.com/poster.jpg",
        seasons=[1, 2, 3],
        size_on_disk=1000000,
        title="Test Media",
    )

    assert media.available_since == datetime(2023, 1, 1)
    assert media.available is True
    assert media.id == 100
    assert media.poster == "http://example.com/poster.jpg"
    assert media.seasons == [1, 2, 3]
    assert media.size_on_disk == 1000000
    assert media.title == "Test Media"


def test_media_info_dto_with_none_available_since():
    media = MediaInfoDTO(
        available_since=None,
        available=False,
        id=100,
        poster="http://example.com/poster.jpg",
        seasons=[],
        size_on_disk=0,
        title="Unavailable Media",
    )

    assert media.available_since is None
    assert media.available is False
    assert media.seasons == []
