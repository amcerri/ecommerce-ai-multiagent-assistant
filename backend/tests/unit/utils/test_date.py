"""
Unit tests for date utilities.

Tests for app.utils.date functions including parsing, formatting,
and date manipulation.
"""

from datetime import datetime, timezone

import pytest

from app.utils.date import (
    format_date,
    format_date_relative,
    get_timezone_aware_now,
    is_valid_date,
    parse_date,
    to_utc,
)


class TestParseDate:
    """Tests for parse_date function."""

    def test_parse_with_format(self) -> None:
        """Test parsing with format string."""
        dt = parse_date("2024-01-01", format="%Y-%m-%d")
        assert isinstance(dt, datetime)
        assert dt.year == 2024
        assert dt.month == 1
        assert dt.day == 1
        assert dt.tzinfo is not None

    def test_parse_without_format(self) -> None:
        """Test parsing without format string."""
        dt = parse_date("2024-01-01 12:00:00")
        assert isinstance(dt, datetime)
        assert dt.year == 2024
        assert dt.tzinfo is not None

    def test_parse_naive_datetime(self) -> None:
        """Test parsing naive datetime (should add UTC)."""
        dt = parse_date("2024-01-01")
        assert dt.tzinfo is not None

    def test_invalid_date(self) -> None:
        """Test invalid date string."""
        with pytest.raises(ValueError):
            parse_date("invalid")

    def test_empty_or_none(self) -> None:
        """Test empty or None date string."""
        with pytest.raises(ValueError):
            parse_date("")
        with pytest.raises(ValueError):
            parse_date(None)  # type: ignore


class TestFormatDate:
    """Tests for format_date function."""

    def test_format_default(self) -> None:
        """Test formatting with default format."""
        dt = datetime(2024, 1, 1, tzinfo=timezone.utc)
        result = format_date(dt)
        assert result == "2024-01-01"

    def test_format_custom(self) -> None:
        """Test formatting with custom format."""
        dt = datetime(2024, 1, 1, 12, 30, 45, tzinfo=timezone.utc)
        result = format_date(dt, format="%Y-%m-%d %H:%M:%S")
        assert result == "2024-01-01 12:30:45"

    def test_format_naive_datetime(self) -> None:
        """Test formatting naive datetime (should assume UTC)."""
        dt = datetime(2024, 1, 1)
        result = format_date(dt)
        assert result == "2024-01-01"

    def test_invalid_datetime(self) -> None:
        """Test invalid datetime object."""
        with pytest.raises(ValueError):
            format_date(None)  # type: ignore


class TestFormatDateRelative:
    """Tests for format_date_relative function."""

    def test_past_seconds(self) -> None:
        """Test relative format for past seconds."""
        now = datetime.now(timezone.utc)
        past = now.replace(second=now.second - 30)
        result = format_date_relative(past, locale="pt-BR")
        assert "segundo" in result.lower()

    def test_future_hours(self) -> None:
        """Test relative format for future hours."""
        now = datetime.now(timezone.utc)
        future = now.replace(hour=now.hour + 2)
        result = format_date_relative(future, locale="pt-BR")
        assert "hora" in result.lower()

    def test_invalid_datetime(self) -> None:
        """Test invalid datetime."""
        result = format_date_relative(None)  # type: ignore
        assert result == "data inválida"

    def test_different_locales(self) -> None:
        """Test different locales."""
        now = datetime.now(timezone.utc)
        past = now.replace(day=now.day - 1)
        result_pt = format_date_relative(past, locale="pt-BR")
        result_en = format_date_relative(past, locale="en-US")
        assert result_pt != result_en


class TestIsValidDate:
    """Tests for is_valid_date function."""

    def test_valid_date(self) -> None:
        """Test valid date string."""
        assert is_valid_date("2024-01-01") is True
        assert is_valid_date("2024-01-01 12:00:00") is True

    def test_invalid_date(self) -> None:
        """Test invalid date string."""
        assert is_valid_date("invalid") is False
        assert is_valid_date("2024-13-01") is False

    def test_empty_or_none(self) -> None:
        """Test empty or None date string."""
        assert is_valid_date("") is False
        assert is_valid_date(None) is False  # type: ignore


class TestGetTimezoneAwareNow:
    """Tests for get_timezone_aware_now function."""

    def test_returns_datetime(self) -> None:
        """Test that function returns datetime."""
        result = get_timezone_aware_now()
        assert isinstance(result, datetime)

    def test_timezone_aware(self) -> None:
        """Test that datetime is timezone-aware."""
        result = get_timezone_aware_now()
        assert result.tzinfo is not None


class TestToUTC:
    """Tests for to_utc function."""

    def test_naive_to_utc(self) -> None:
        """Test converting naive datetime to UTC."""
        dt = datetime(2024, 1, 1, 12, 0, 0)
        result = to_utc(dt)
        assert result.tzinfo == timezone.utc

    def test_timezone_aware_to_utc(self) -> None:
        """Test converting timezone-aware datetime to UTC."""
        from zoneinfo import ZoneInfo

        dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))
        result = to_utc(dt)
        assert result.tzinfo == timezone.utc

    def test_invalid_datetime(self) -> None:
        """Test invalid datetime object."""
        with pytest.raises(ValueError):
            to_utc(None)  # type: ignore

