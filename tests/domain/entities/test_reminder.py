"""Tests for Reminder domain entity."""

from datetime import UTC, datetime

import pytest

from scruffy.domain.entities.reminder import Reminder


def test_reminder_creation():
    """Test Reminder entity can be created."""
    reminder = Reminder(
        request_id=1,
        user_id=100,
        date_sent=datetime.now(UTC),
    )

    assert reminder.request_id == 1
    assert reminder.user_id == 100
    assert reminder.date_sent is not None


def test_reminder_is_immutable():
    """Test Reminder entity is immutable (frozen dataclass)."""
    reminder = Reminder(
        request_id=1,
        user_id=100,
        date_sent=datetime.now(UTC),
    )

    with pytest.raises(Exception):  # noqa: PT011
        reminder.user_id = 200
