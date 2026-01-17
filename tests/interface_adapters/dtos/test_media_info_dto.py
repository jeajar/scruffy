"""Tests for MediaInfoDTO."""

from datetime import UTC, datetime

import pytest

from scruffy.interface_adapters.dtos.media_info_dto import MediaInfoDTO


def test_media_info_dto_creation():
    """Test MediaInfoDTO can be created."""
    dto = MediaInfoDTO(
        id=1,
        title="Test Movie",
        available=True,
        available_since=datetime.now(UTC),
        size_on_disk=1000000,
        poster="http://example.com/poster.jpg",
        seasons=[],
    )

    assert dto.id == 1
    assert dto.title == "Test Movie"
    assert dto.available is True
    assert dto.available_since is not None
    assert dto.size_on_disk == 1000000
    assert dto.poster == "http://example.com/poster.jpg"
    assert dto.seasons == []


def test_media_info_dto_is_immutable():
    """Test MediaInfoDTO is immutable (frozen dataclass)."""
    dto = MediaInfoDTO(
        id=1,
        title="Test Movie",
        available=True,
        available_since=datetime.now(UTC),
        size_on_disk=1000000,
        poster="http://example.com/poster.jpg",
        seasons=[],
    )

    with pytest.raises(Exception):  # noqa: PT011
        dto.title = "Changed"


def test_media_info_dto_with_none_available_since():
    """Test MediaInfoDTO with None available_since."""
    dto = MediaInfoDTO(
        id=1,
        title="Unavailable Movie",
        available=False,
        available_since=None,
        size_on_disk=0,
        poster="",
        seasons=[],
    )

    assert dto.available_since is None
    assert dto.available is False


def test_media_info_dto_with_seasons():
    """Test MediaInfoDTO with seasons (for TV shows)."""
    dto = MediaInfoDTO(
        id=1,
        title="Test Series",
        available=True,
        available_since=datetime.now(UTC),
        size_on_disk=2000000,
        poster="http://example.com/poster.jpg",
        seasons=[1, 2, 3],
    )

    assert dto.seasons == [1, 2, 3]
