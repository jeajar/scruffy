"""Tests for MediaRequest domain entity."""

import dataclasses
from datetime import UTC, datetime

import pytest

from scruffy.domain.entities.media_request import MediaRequest
from scruffy.domain.value_objects.media_status import MediaStatus
from scruffy.domain.value_objects.media_type import MediaType
from scruffy.domain.value_objects.request_status import RequestStatus


def test_media_request_creation():
    """Test MediaRequest entity can be created."""
    request = MediaRequest(
        user_id=1,
        user_email="test@example.com",
        media_type=MediaType.MOVIE,
        request_id=100,
        request_status=RequestStatus.APPROVED,
        updated_at=datetime.now(UTC),
        media_id=99,
        media_status=MediaStatus.AVAILABLE,
        external_service_id=1000,
        seasons=[],
    )

    assert request.user_id == 1
    assert request.user_email == "test@example.com"
    assert request.media_type == MediaType.MOVIE
    assert request.request_id == 100
    assert request.request_status == RequestStatus.APPROVED
    assert request.media_id == 99
    assert request.media_status == MediaStatus.AVAILABLE
    assert request.external_service_id == 1000
    assert request.seasons == []


def test_media_request_is_immutable():
    """Test MediaRequest entity is immutable (frozen dataclass)."""
    request = MediaRequest(
        user_id=1,
        user_email="test@example.com",
        media_type=MediaType.MOVIE,
        request_id=100,
        request_status=RequestStatus.APPROVED,
        updated_at=datetime.now(UTC),
        media_id=99,
        media_status=MediaStatus.AVAILABLE,
        external_service_id=1000,
        seasons=[],
    )

    with pytest.raises(dataclasses.FrozenInstanceError):
        request.user_email = "changed@example.com"  # ty: ignore[invalid-assignment]


def test_media_request_tv_with_seasons():
    """Test MediaRequest entity for TV shows with seasons."""
    request = MediaRequest(
        user_id=2,
        user_email="tv@example.com",
        media_type=MediaType.TV,
        request_id=200,
        request_status=RequestStatus.APPROVED,
        updated_at=datetime.now(UTC),
        media_id=100,
        media_status=MediaStatus.PARTIALLY_AVAILABLE,
        external_service_id=2000,
        seasons=[1, 2],
    )

    assert request.media_type == MediaType.TV
    assert request.seasons == [1, 2]
    assert request.media_status == MediaStatus.PARTIALLY_AVAILABLE
