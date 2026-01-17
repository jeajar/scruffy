"""Tests for MediaType value object."""

from scruffy.domain.value_objects.media_type import MediaType


def test_media_type_enum_values():
    """Test MediaType enum has expected values."""
    assert MediaType.MOVIE.value == "movie"
    assert MediaType.TV.value == "tv"


def test_media_type_enum_names():
    """Test MediaType enum has expected names."""
    assert MediaType.MOVIE.name == "MOVIE"
    assert MediaType.TV.name == "TV"
