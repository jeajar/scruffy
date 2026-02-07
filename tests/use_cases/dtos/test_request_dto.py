"""Tests for RequestDTO."""

import dataclasses
from datetime import UTC, datetime

import pytest

from scruffy.domain.value_objects.media_status import MediaStatus
from scruffy.domain.value_objects.request_status import RequestStatus
from scruffy.use_cases.dtos.request_dto import RequestDTO


def test_request_dto_creation():
    """Test RequestDTO can be created."""
    dto = RequestDTO(
        user_id=1,
        user_email="test@example.com",
        type="movie",
        request_id=100,
        request_status=RequestStatus.PENDING_APPROVAL,
        updated_at=datetime.now(UTC),
        media_status=MediaStatus.AVAILABLE,
        media_id=99,
        external_service_id=1000,
        seasons=[],
    )

    assert dto.user_id == 1
    assert dto.user_email == "test@example.com"
    assert dto.type == "movie"
    assert dto.request_id == 100
    assert dto.media_id == 99
    assert dto.request_status == RequestStatus.PENDING_APPROVAL
    assert dto.media_status == MediaStatus.AVAILABLE
    assert dto.external_service_id == 1000
    assert dto.seasons == []


def test_request_dto_is_immutable():
    """Test RequestDTO is immutable (frozen dataclass)."""
    dto = RequestDTO(
        user_id=1,
        user_email="test@example.com",
        type="movie",
        request_id=100,
        request_status=RequestStatus.APPROVED,
        updated_at=datetime.now(UTC),
        media_status=MediaStatus.AVAILABLE,
        media_id=99,
        external_service_id=1000,
        seasons=[],
    )

    with pytest.raises(dataclasses.FrozenInstanceError):
        dto.user_email = "changed@example.com"  # ty: ignore[invalid-assignment]


def test_from_overseer_response_movie():
    """Test from_overseer_response parses movie request correctly."""
    response = {
        "requestedBy": {"id": 1, "email": "test@example.com"},
        "type": "movie",
        "id": 100,
        "status": "approved",
        "media": {
            "status": "available",
            "externalServiceId": 1000,
            "updatedAt": "2023-01-01T12:00:00Z",
            "id": 99,
        },
    }

    dto = RequestDTO.from_overseer_response(response)

    assert dto.user_id == 1
    assert dto.user_email == "test@example.com"
    assert dto.type == "movie"
    assert dto.request_id == 100
    assert dto.seasons == []
    assert dto.updated_at == datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC)
    assert dto.request_status == RequestStatus.APPROVED
    assert dto.media_status == MediaStatus.AVAILABLE
    assert dto.external_service_id == 1000
    assert dto.media_id == 99


def test_from_overseer_response_tv():
    """Test from_overseer_response parses TV request correctly."""
    response = {
        "requestedBy": {"id": 2, "email": "tv@example.com"},
        "type": "tv",
        "id": 200,
        "status": "approved",
        "media": {
            "status": "processing",
            "externalServiceId": 2000,
            "updatedAt": "2023-02-01T12:00:00Z",
            "id": 100,
        },
        "seasons": [{"seasonNumber": 1}, {"seasonNumber": 2}],
    }

    dto = RequestDTO.from_overseer_response(response)

    assert dto.user_id == 2
    assert dto.type == "tv"
    assert dto.seasons == [1, 2]
    assert dto.media_status == MediaStatus.PROCESSING


def test_from_overseer_response_status_mapping():
    """Test from_overseer_response maps statuses correctly."""
    # Test pendingApproval
    response_pending = {
        "requestedBy": {"id": 1, "email": "test@example.com"},
        "type": "movie",
        "id": 1,
        "status": "pendingApproval",
        "media": {
            "status": "pending",
            "externalServiceId": 1000,
            "updatedAt": "2023-01-01T12:00:00Z",
            "id": 99,
        },
    }
    dto = RequestDTO.from_overseer_response(response_pending)
    assert dto.request_status == RequestStatus.PENDING_APPROVAL
    assert dto.media_status == MediaStatus.PENDING

    # Test declined
    response_declined = {
        "requestedBy": {"id": 1, "email": "test@example.com"},
        "type": "movie",
        "id": 1,
        "status": "declined",
        "media": {
            "status": "unknown",
            "externalServiceId": 1000,
            "updatedAt": "2023-01-01T12:00:00Z",
            "id": 99,
        },
    }
    dto = RequestDTO.from_overseer_response(response_declined)
    assert dto.request_status == RequestStatus.DECLINED
    assert dto.media_status == MediaStatus.UNKNOWN


def test_from_overseer_response_partially_available():
    """Test from_overseer_response handles partiallyAvailable status."""
    response = {
        "requestedBy": {"id": 1, "email": "test@example.com"},
        "type": "tv",
        "id": 1,
        "status": "approved",
        "media": {
            "status": "partiallyAvailable",
            "externalServiceId": 1000,
            "updatedAt": "2023-01-01T12:00:00Z",
            "id": 99,
        },
        "seasons": [{"seasonNumber": 1}],
    }

    dto = RequestDTO.from_overseer_response(response)
    assert dto.media_status == MediaStatus.PARTIALLY_AVAILABLE


def test_json_serialization():
    """Test json() method serializes DTO correctly."""
    dto = RequestDTO(
        user_id=1,
        user_email="test@example.com",
        type="movie",
        request_id=100,
        request_status=RequestStatus.APPROVED,
        updated_at=datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC),
        media_status=MediaStatus.AVAILABLE,
        media_id=99,
        external_service_id=1000,
        seasons=[],
    )

    json_data = dto.json()

    assert json_data["user_id"] == 1
    assert json_data["user_email"] == "test@example.com"
    assert json_data["type"] == "movie"
    assert json_data["request_id"] == 100
    assert json_data["request_status"] == "APPROVED"
    assert json_data["media_status"] == "AVAILABLE"
    assert json_data["seasons"] == []


def test_json_serialization_with_seasons():
    """Test json() method serializes seasons correctly."""
    dto = RequestDTO(
        user_id=1,
        user_email="test@example.com",
        type="tv",
        request_id=100,
        request_status=RequestStatus.APPROVED,
        updated_at=datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC),
        media_status=MediaStatus.AVAILABLE,
        media_id=99,
        external_service_id=1000,
        seasons=[1, 2, 3],
    )

    json_data = dto.json()

    assert json_data["seasons"] == [1, 2, 3]
