"""
tests/unit/test_formatters.py — Unit tests for bot/formatters.py
"""
from bot.formatters import format_response


class TestFormatResponse:
    def test_normal_text(self):
        assert format_response("Hello world") == "Hello world"

    def test_strips_whitespace(self):
        assert format_response("  hello  ") == "hello"

    def test_empty_string_returns_fallback(self):
        result = format_response("")
        assert "Maaf" in result

    def test_none_returns_fallback(self):
        result = format_response(None)
        assert "Maaf" in result
