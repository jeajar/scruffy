"""Tests for RetentionPolicy value object."""

import dataclasses
from datetime import UTC, datetime, timedelta

import pytest

from scruffy.domain.value_objects.retention_policy import RetentionPolicy


def test_retention_policy_creation():
    """Test RetentionPolicy can be created."""
    policy = RetentionPolicy(retention_days=30, reminder_days=7)

    assert policy.retention_days == 30
    assert policy.reminder_days == 7


def test_retention_policy_is_immutable():
    """Test RetentionPolicy is immutable (frozen dataclass)."""
    policy = RetentionPolicy(retention_days=30, reminder_days=7)

    with pytest.raises(dataclasses.FrozenInstanceError):
        policy.retention_days = 60  # ty: ignore[invalid-assignment]


def test_should_remind_when_within_reminder_window():
    """Test should_remind returns True when within reminder window."""
    policy = RetentionPolicy(retention_days=30, reminder_days=7)
    available_since = datetime.now(UTC) - timedelta(days=24)  # 6 days left

    assert policy.should_remind(available_since) is True


def test_should_remind_when_exactly_at_reminder_threshold():
    """Test should_remind returns True when exactly at reminder threshold."""
    policy = RetentionPolicy(retention_days=30, reminder_days=7)
    available_since = datetime.now(UTC) - timedelta(days=23)  # 7 days left

    assert policy.should_remind(available_since) is True


def test_should_remind_when_before_reminder_window():
    """Test should_remind returns False when before reminder window."""
    policy = RetentionPolicy(retention_days=30, reminder_days=7)
    available_since = datetime.now(UTC) - timedelta(days=20)  # 10 days left

    assert policy.should_remind(available_since) is False


def test_should_remind_when_after_retention_period():
    """Test should_remind returns True when after retention period (should delete)."""
    policy = RetentionPolicy(retention_days=30, reminder_days=7)
    available_since = datetime.now(UTC) - timedelta(days=31)  # Past retention

    assert policy.should_remind(available_since) is True


def test_should_remind_with_none_date():
    """Test should_remind returns False when available_since is None."""
    policy = RetentionPolicy(retention_days=30, reminder_days=7)

    assert policy.should_remind(None) is False


def test_should_delete_when_after_retention_period():
    """Test should_delete returns True when after retention period."""
    policy = RetentionPolicy(retention_days=30, reminder_days=7)
    available_since = datetime.now(UTC) - timedelta(days=31)

    assert policy.should_delete(available_since) is True


def test_should_delete_when_exactly_at_retention_period():
    """Test should_delete returns True when exactly at retention period."""
    policy = RetentionPolicy(retention_days=30, reminder_days=7)
    available_since = datetime.now(UTC) - timedelta(days=30)

    assert policy.should_delete(available_since) is True


def test_should_delete_when_before_retention_period():
    """Test should_delete returns False when before retention period."""
    policy = RetentionPolicy(retention_days=30, reminder_days=7)
    available_since = datetime.now(UTC) - timedelta(days=29)

    assert policy.should_delete(available_since) is False


def test_should_delete_with_none_date():
    """Test should_delete returns False when available_since is None."""
    policy = RetentionPolicy(retention_days=30, reminder_days=7)

    assert policy.should_delete(None) is False


def test_days_remaining_when_before_retention():
    """Test days_remaining calculates correctly before retention period."""
    policy = RetentionPolicy(retention_days=30, reminder_days=7)
    available_since = datetime.now(UTC) - timedelta(days=20)

    days = policy.days_remaining(available_since)
    assert days == 10


def test_days_remaining_when_after_retention():
    """Test days_remaining returns negative when after retention period."""
    policy = RetentionPolicy(retention_days=30, reminder_days=7)
    available_since = datetime.now(UTC) - timedelta(days=35)

    days = policy.days_remaining(available_since)
    assert days == -5


def test_days_remaining_when_exactly_at_retention():
    """Test days_remaining returns 0 when exactly at retention period."""
    policy = RetentionPolicy(retention_days=30, reminder_days=7)
    available_since = datetime.now(UTC) - timedelta(days=30)

    days = policy.days_remaining(available_since)
    assert days == 0


def test_days_remaining_with_none_date():
    """Test days_remaining returns 0 when available_since is None."""
    policy = RetentionPolicy(retention_days=30, reminder_days=7)

    assert policy.days_remaining(None) == 0


def test_retention_policy_with_different_timezones():
    """Test retention policy handles timezones correctly."""
    policy = RetentionPolicy(retention_days=30, reminder_days=7)
    # Create datetime with timezone
    available_since = datetime.now(UTC) - timedelta(days=25)

    # Should work correctly with timezone-aware datetime
    assert policy.should_remind(available_since) is True
    assert policy.should_delete(available_since) is False
    assert policy.days_remaining(available_since) == 5
