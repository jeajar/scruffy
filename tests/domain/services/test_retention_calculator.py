"""Tests for RetentionCalculator domain service."""

from datetime import UTC, datetime, timedelta

import pytest

from scruffy.domain.entities.media import Media
from scruffy.domain.services.retention_calculator import (
    RetentionCalculator,
    RetentionResult,
)
from scruffy.domain.value_objects.retention_policy import RetentionPolicy


def test_retention_calculator_initialization(retention_policy):
    """Test RetentionCalculator can be initialized with policy."""
    calculator = RetentionCalculator(retention_policy)

    assert calculator.policy == retention_policy


def test_evaluate_unavailable_media(retention_policy):
    """Test evaluate returns no action for unavailable media."""
    calculator = RetentionCalculator(retention_policy)
    media = Media(
        id=1,
        title="Test Movie",
        available=False,
        available_since=None,
        size_on_disk=0,
        poster="",
        seasons=[],
    )

    result = calculator.evaluate(media)

    assert isinstance(result, RetentionResult)
    assert result.remind is False
    assert result.delete is False
    assert result.days_left == 0


def test_evaluate_media_with_none_available_since(retention_policy):
    """Test evaluate returns no action when available_since is None."""
    calculator = RetentionCalculator(retention_policy)
    media = Media(
        id=1,
        title="Test Movie",
        available=True,
        available_since=None,
        size_on_disk=1000000,
        poster="",
        seasons=[],
    )

    result = calculator.evaluate(media)

    assert result.remind is False
    assert result.delete is False
    assert result.days_left == 0


def test_evaluate_media_should_delete(retention_policy):
    """Test evaluate returns delete=True for media past retention period."""
    calculator = RetentionCalculator(retention_policy)
    media = Media(
        id=1,
        title="Test Movie",
        available=True,
        available_since=datetime.now(UTC) - timedelta(days=31),
        size_on_disk=1000000,
        poster="",
        seasons=[],
    )

    result = calculator.evaluate(media)

    assert result.delete is True
    assert result.remind is True  # Should also remind when deleting
    assert result.days_left < 0


def test_evaluate_media_should_remind(retention_policy):
    """Test evaluate returns remind=True for media within reminder window."""
    calculator = RetentionCalculator(retention_policy)
    media = Media(
        id=1,
        title="Test Movie",
        available=True,
        available_since=datetime.now(UTC) - timedelta(days=24),
        size_on_disk=1000000,
        poster="",
        seasons=[],
    )

    result = calculator.evaluate(media)

    assert result.remind is True
    assert result.delete is False
    assert result.days_left == 6


def test_evaluate_media_no_action_needed(retention_policy):
    """Test evaluate returns no action for media before reminder window."""
    calculator = RetentionCalculator(retention_policy)
    media = Media(
        id=1,
        title="Test Movie",
        available=True,
        available_since=datetime.now(UTC) - timedelta(days=20),
        size_on_disk=1000000,
        poster="",
        seasons=[],
    )

    result = calculator.evaluate(media)

    assert result.remind is False
    assert result.delete is False
    assert result.days_left == 10


def test_evaluate_media_at_retention_boundary(retention_policy):
    """Test evaluate at exact retention boundary."""
    calculator = RetentionCalculator(retention_policy)
    media = Media(
        id=1,
        title="Test Movie",
        available=True,
        available_since=datetime.now(UTC) - timedelta(days=30),
        size_on_disk=1000000,
        poster="",
        seasons=[],
    )

    result = calculator.evaluate(media)

    assert result.delete is True
    assert result.days_left == 0


def test_evaluate_media_at_reminder_boundary(retention_policy):
    """Test evaluate at exact reminder boundary."""
    calculator = RetentionCalculator(retention_policy)
    media = Media(
        id=1,
        title="Test Movie",
        available=True,
        available_since=datetime.now(UTC) - timedelta(days=23),
        size_on_disk=1000000,
        poster="",
        seasons=[],
    )

    result = calculator.evaluate(media)

    assert result.remind is True
    assert result.delete is False
    assert result.days_left == 7


def test_evaluate_with_custom_policy():
    """Test evaluate with custom retention policy."""
    custom_policy = RetentionPolicy(retention_days=60, reminder_days=14)
    calculator = RetentionCalculator(custom_policy)
    media = Media(
        id=1,
        title="Test Movie",
        available=True,
        available_since=datetime.now(UTC) - timedelta(days=50),
        size_on_disk=1000000,
        poster="",
        seasons=[],
    )

    result = calculator.evaluate(media)

    assert result.remind is True
    assert result.delete is False
    assert result.days_left == 10
