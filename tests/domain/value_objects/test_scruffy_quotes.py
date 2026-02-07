"""Tests for ScruffyQuotes value object."""

from scruffy.domain.value_objects import SCRUFFY_QUOTES, ScruffyQuotes


class TestScruffyQuotes:
    """Tests for the ScruffyQuotes value object."""

    def test_random_returns_string(self):
        """Test that random() returns a non-empty string."""
        quote = SCRUFFY_QUOTES.random()
        assert isinstance(quote, str)
        assert len(quote) > 0

    def test_random_returns_one_of_quotes(self):
        """Test that random() returns one of the known quotes."""
        quotes = ScruffyQuotes()
        for _ in range(50):  # Sample multiple times
            quote = quotes.random()
            assert quote in quotes._quotes

    def test_quotes_are_email_safe(self):
        """Test that quotes don't contain problematic characters for email bodies."""
        invalid_chars = ["\x00", "\n", "\r"]
        for quote in SCRUFFY_QUOTES._quotes:
            for char in invalid_chars:
                assert char not in quote, f"Quote contains invalid character: {char}"
