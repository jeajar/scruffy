from scruffy.quotes import scruffy_quotes


def test_quotes_is_list():
    assert isinstance(scruffy_quotes, list)


def test_quotes_not_empty():
    assert len(scruffy_quotes) > 0


def test_quotes_are_strings():
    for quote in scruffy_quotes:
        assert isinstance(quote, str)
        assert len(quote) > 0


def test_quotes_are_email_safe():
    # Check for potentially problematic characters in email bodies
    invalid_chars = ["\x00", "\n", "\r"]

    for quote in scruffy_quotes:
        for char in invalid_chars:
            assert char not in quote, f"Quote contains invalid character: {char}"
