"""Tests for ExtensionStore."""

import pytest

from scruffy.frameworks_and_drivers.database.extension_store import ExtensionStore


@pytest.fixture
def store(in_memory_engine):
    """Create ExtensionStore with in-memory engine."""
    return ExtensionStore(in_memory_engine)


def test_is_extended_when_not_exists(store):
    """Test is_extended returns False when no extension record."""
    assert store.is_extended(1) is False


def test_extend_request_creates_record(store):
    """Test extend_request creates record and returns True."""
    result = store.extend_request(1, plex_user_id=100)

    assert result is True
    assert store.is_extended(1) is True


def test_extend_request_idempotent(store):
    """Test extend_request returns False when already extended."""
    store.extend_request(1, plex_user_id=100)
    result = store.extend_request(1, plex_user_id=200)

    assert result is False
    assert store.is_extended(1) is True


def test_get_extended_request_ids(store):
    """Test get_extended_request_ids returns all extended request IDs."""
    store.extend_request(1, plex_user_id=100)
    store.extend_request(3, plex_user_id=100)

    ids = store.get_extended_request_ids()

    assert ids == {1, 3}


def test_get_extended_request_ids_empty(store):
    """Test get_extended_request_ids returns empty set when none extended."""
    ids = store.get_extended_request_ids()

    assert ids == set()


def test_get_extension_days_default(store):
    """Test get_extension_days returns 0 when no provider given."""
    assert store.get_extension_days() == 0


def test_get_extension_days_from_provider(in_memory_engine):
    """Test get_extension_days returns value from injected provider."""
    store = ExtensionStore(
        in_memory_engine,
        extension_days_provider=lambda: 14,
    )
    assert store.get_extension_days() == 14
