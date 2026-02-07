"""Tests for ReminderGateway."""

import pytest

from scruffy.frameworks_and_drivers.database.reminder_model import ReminderModel
from scruffy.interface_adapters.gateways.reminder_gateway import ReminderGateway


@pytest.fixture
def gateway(in_memory_engine):
    """Create ReminderGateway instance with in-memory database."""
    return ReminderGateway(in_memory_engine)


def test_has_reminder_when_not_exists(gateway):
    """Test has_reminder returns False when reminder doesn't exist."""
    assert gateway.has_reminder(request_id=1) is False


def test_has_reminder_when_exists(gateway, in_memory_engine):
    """Test has_reminder returns True when reminder exists."""
    from sqlmodel import Session

    # Add reminder directly to database
    with Session(in_memory_engine) as session:
        reminder = ReminderModel(request_id=1, user_id=1)
        session.add(reminder)
        session.commit()

    assert gateway.has_reminder(request_id=1) is True


def test_add_reminder(gateway):
    """Test add_reminder creates reminder record."""
    gateway.add_reminder(request_id=1, user_id=1)

    assert gateway.has_reminder(request_id=1) is True


def test_add_reminder_multiple_times(gateway):
    """Test adding multiple reminders."""
    gateway.add_reminder(request_id=1, user_id=1)
    gateway.add_reminder(request_id=2, user_id=1)

    assert gateway.has_reminder(request_id=1) is True
    assert gateway.has_reminder(request_id=2) is True


def test_has_reminder_with_multiple_entries(gateway):
    """Test has_reminder with multiple entries in database."""
    gateway.add_reminder(request_id=1, user_id=1)
    gateway.add_reminder(request_id=2, user_id=1)

    assert gateway.has_reminder(request_id=1) is True
    assert gateway.has_reminder(request_id=2) is True
    assert gateway.has_reminder(request_id=3) is False


def test_gateway_initialization_default_engine():
    """Test gateway initialization with default engine."""
    gateway = ReminderGateway()

    # Should not raise error
    assert gateway.has_reminder(request_id=999) is False


def test_get_request_ids_with_reminders_empty_list(gateway):
    """Test get_request_ids_with_reminders returns empty set for empty input."""
    assert gateway.get_request_ids_with_reminders([]) == set()


def test_get_request_ids_with_reminders_none_exist(gateway):
    """Test get_request_ids_with_reminders returns empty set when no reminders exist."""
    result = gateway.get_request_ids_with_reminders([1, 2, 3])
    assert result == set()


def test_get_request_ids_with_reminders_some_exist(gateway):
    """Test get_request_ids_with_reminders returns only IDs that have reminders."""
    gateway.add_reminder(request_id=1, user_id=1)
    gateway.add_reminder(request_id=3, user_id=1)

    result = gateway.get_request_ids_with_reminders([1, 2, 3, 4])
    assert result == {1, 3}


def test_get_request_ids_with_reminders_all_exist(gateway):
    """Test get_request_ids_with_reminders when all requested IDs have reminders."""
    gateway.add_reminder(request_id=1, user_id=1)
    gateway.add_reminder(request_id=2, user_id=1)

    result = gateway.get_request_ids_with_reminders([1, 2])
    assert result == {1, 2}
