"""Tests for Scruffy quotes utility."""

import pytest

from scruffy.frameworks_and_drivers.utils.quotes import scruffy_quotes


class TestScruffyQuotes:
    """Tests for the scruffy_quotes list."""

    def test_quotes_is_list(self):
        """Test that scruffy_quotes is a list."""
        assert isinstance(scruffy_quotes, list)

    def test_quotes_not_empty(self):
        """Test that quotes list is not empty."""
        assert len(scruffy_quotes) > 0

    def test_quotes_are_strings(self):
        """Test that all quotes are non-empty strings."""
        for quote in scruffy_quotes:
            assert isinstance(quote, str)
            assert len(quote) > 0

    def test_quotes_are_email_safe(self):
        """Test that quotes don't contain problematic characters for email bodies."""
        # Check for potentially problematic characters in email bodies
        invalid_chars = ["\x00", "\n", "\r"]

        for quote in scruffy_quotes:
            for char in invalid_chars:
                assert char not in quote, f"Quote contains invalid character: {char}"
