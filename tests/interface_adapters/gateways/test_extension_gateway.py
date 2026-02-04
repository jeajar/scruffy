"""Tests for ExtensionGateway."""

import pytest

from scruffy.frameworks_and_drivers.database.extension_model import (
    RequestExtensionModel,
)
from scruffy.interface_adapters.gateways.extension_gateway import ExtensionGateway


@pytest.fixture
def gateway(in_memory_engine):
    """Create ExtensionGateway with in-memory engine."""
    return ExtensionGateway(in_memory_engine)


def test_is_extended_when_not_exists(gateway):
    """Test is_extended returns False when no extension record."""
    assert gateway.is_extended(1) is False


def test_extend_request_creates_record(gateway):
    """Test extend_request creates record and returns True."""
    result = gateway.extend_request(1, plex_user_id=100)

    assert result is True
    assert gateway.is_extended(1) is True


def test_extend_request_idempotent(gateway):
    """Test extend_request returns False when already extended."""
    gateway.extend_request(1, plex_user_id=100)
    result = gateway.extend_request(1, plex_user_id=200)

    assert result is False
    assert gateway.is_extended(1) is True


def test_get_extended_request_ids(gateway):
    """Test get_extended_request_ids returns all extended request IDs."""
    gateway.extend_request(1, plex_user_id=100)
    gateway.extend_request(3, plex_user_id=100)

    ids = gateway.get_extended_request_ids()

    assert ids == {1, 3}


def test_get_extended_request_ids_empty(gateway):
    """Test get_extended_request_ids returns empty set when none extended."""
    ids = gateway.get_extended_request_ids()

    assert ids == set()
