"""Tests for MediaStatus value object."""

from scruffy.domain.value_objects.media_status import MediaStatus


def test_media_status_enum_values():
    """Test MediaStatus enum has expected values."""
    assert MediaStatus.UNKNOWN.value == 1
    assert MediaStatus.PENDING.value == 2
    assert MediaStatus.PROCESSING.value == 3
    assert MediaStatus.PARTIALLY_AVAILABLE.value == 4
    assert MediaStatus.AVAILABLE.value == 5


def test_media_status_enum_names():
    """Test MediaStatus enum has expected names."""
    assert MediaStatus.UNKNOWN.name == "UNKNOWN"
    assert MediaStatus.PENDING.name == "PENDING"
    assert MediaStatus.PROCESSING.name == "PROCESSING"
    assert MediaStatus.PARTIALLY_AVAILABLE.name == "PARTIALLY_AVAILABLE"
    assert MediaStatus.AVAILABLE.name == "AVAILABLE"
