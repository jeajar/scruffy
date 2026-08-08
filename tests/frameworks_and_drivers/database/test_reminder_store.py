"""Tests for ReminderStore."""

import pytest

from scruffy.frameworks_and_drivers.database.reminder_model import ReminderModel
from scruffy.frameworks_and_drivers.database.reminder_store import ReminderStore


@pytest.fixture
def store(in_memory_engine):
    """Create ReminderStore instance with in-memory database."""
    return ReminderStore(in_memory_engine)


def test_has_reminder_when_not_exists(store):
    """Test has_reminder returns False when reminder doesn't exist."""
    assert store.has_reminder(request_id=1) is False


def test_has_reminder_when_exists(store, in_memory_engine):
    """Test has_reminder returns True when reminder exists."""
    from sqlmodel import Session

    # Add reminder directly to database
    with Session(in_memory_engine) as session:
        reminder = ReminderModel(request_id=1, user_id=1)
        session.add(reminder)
        session.commit()

    assert store.has_reminder(request_id=1) is True


def test_add_reminder(store):
    """Test add_reminder creates reminder record."""
    store.add_reminder(request_id=1, user_id=1)

    assert store.has_reminder(request_id=1) is True


def test_add_reminder_multiple_times(store):
    """Test adding multiple reminders."""
    store.add_reminder(request_id=1, user_id=1)
    store.add_reminder(request_id=2, user_id=1)

    assert store.has_reminder(request_id=1) is True
    assert store.has_reminder(request_id=2) is True


def test_has_reminder_with_multiple_entries(store):
    """Test has_reminder with multiple entries in database."""
    store.add_reminder(request_id=1, user_id=1)
    store.add_reminder(request_id=2, user_id=1)

    assert store.has_reminder(request_id=1) is True
    assert store.has_reminder(request_id=2) is True
    assert store.has_reminder(request_id=3) is False


def test_store_initialization_default_engine():
    """Test store initialization with default engine."""
    store = ReminderStore()

    # Should not raise error
    assert store.has_reminder(request_id=999) is False


def test_get_request_ids_with_reminders_empty_list(store):
    """Test get_request_ids_with_reminders returns empty set for empty input."""
    assert store.get_request_ids_with_reminders([]) == set()


def test_get_request_ids_with_reminders_none_exist(store):
    """Test get_request_ids_with_reminders returns empty set when no reminders exist."""
    result = store.get_request_ids_with_reminders([1, 2, 3])
    assert result == set()


def test_get_request_ids_with_reminders_some_exist(store):
    """Test get_request_ids_with_reminders returns only IDs that have reminders."""
    store.add_reminder(request_id=1, user_id=1)
    store.add_reminder(request_id=3, user_id=1)

    result = store.get_request_ids_with_reminders([1, 2, 3, 4])
    assert result == {1, 3}


def test_get_request_ids_with_reminders_all_exist(store):
    """Test get_request_ids_with_reminders when all requested IDs have reminders."""
    store.add_reminder(request_id=1, user_id=1)
    store.add_reminder(request_id=2, user_id=1)

    result = store.get_request_ids_with_reminders([1, 2])
    assert result == {1, 2}
