"""Tests for Media domain entity."""

import dataclasses
from datetime import UTC, datetime

import pytest

from scruffy.domain.entities.media import Media


def test_media_creation():
    """Test Media entity can be created."""
    media = Media(
        id=1,
        title="Test Movie",
        available=True,
        available_since=datetime.now(UTC),
        size_on_disk=1000000,
        poster="http://example.com/poster.jpg",
        seasons=[],
    )

    assert media.id == 1
    assert media.title == "Test Movie"
    assert media.available is True
    assert media.available_since is not None
    assert media.size_on_disk == 1000000
    assert media.poster == "http://example.com/poster.jpg"
    assert media.seasons == []


def test_media_is_immutable():
    """Test Media entity is immutable (frozen dataclass)."""
    media = Media(
        id=1,
        title="Test Movie",
        available=True,
        available_since=datetime.now(UTC),
        size_on_disk=1000000,
        poster="http://example.com/poster.jpg",
        seasons=[],
    )

    with pytest.raises(dataclasses.FrozenInstanceError):
        media.title = "Changed"  # ty: ignore[invalid-assignment]


def test_is_available_when_available_and_has_date():
    """Test is_available returns True when available and has available_since."""
    media = Media(
        id=1,
        title="Test Movie",
        available=True,
        available_since=datetime.now(UTC),
        size_on_disk=1000000,
        poster="http://example.com/poster.jpg",
        seasons=[],
    )

    assert media.is_available() is True


def test_is_available_when_not_available():
    """Test is_available returns False when available is False."""
    media = Media(
        id=1,
        title="Test Movie",
        available=False,
        available_since=datetime.now(UTC),
        size_on_disk=1000000,
        poster="http://example.com/poster.jpg",
        seasons=[],
    )

    assert media.is_available() is False


def test_is_available_when_no_available_since():
    """Test is_available returns False when available_since is None."""
    media = Media(
        id=1,
        title="Test Movie",
        available=True,
        available_since=None,
        size_on_disk=1000000,
        poster="http://example.com/poster.jpg",
        seasons=[],
    )

    assert media.is_available() is False


def test_is_available_when_not_available_and_no_date():
    """Test is_available returns False when both available is False and date is None."""
    media = Media(
        id=1,
        title="Test Movie",
        available=False,
        available_since=None,
        size_on_disk=1000000,
        poster="http://example.com/poster.jpg",
        seasons=[],
    )

    assert media.is_available() is False


def test_media_with_seasons():
    """Test Media entity with seasons (for TV shows)."""
    media = Media(
        id=1,
        title="Test Series",
        available=True,
        available_since=datetime.now(UTC),
        size_on_disk=2000000,
        poster="http://example.com/poster.jpg",
        seasons=[1, 2, 3],
    )

    assert media.seasons == [1, 2, 3]
    assert media.is_available() is True
