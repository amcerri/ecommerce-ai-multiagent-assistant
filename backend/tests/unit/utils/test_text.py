"""
Unit tests for text processing utilities.

Tests for app.utils.text functions including normalization, truncation,
cleaning, sentence extraction, and word/character counting.
"""

import pytest

from app.utils.text import (
    char_count,
    clean_text,
    extract_sentences,
    normalize_text,
    truncate_text,
    word_count,
)


class TestNormalizeText:
    """Tests for normalize_text function."""

    def test_normalize_spaces(self) -> None:
        """Test normalization of multiple spaces."""
        assert normalize_text("hello    world") == "hello world"
        assert normalize_text("  hello   world  ") == "hello world"

    def test_normalize_line_breaks(self) -> None:
        """Test normalization of line breaks."""
        assert normalize_text("hello\r\nworld") == "hello\nworld"
        assert normalize_text("hello\rworld") == "hello\nworld"
        assert normalize_text("hello\n\n\nworld") == "hello\nworld"

    def test_empty_or_none(self) -> None:
        """Test empty or None text."""
        assert normalize_text("") == ""
        assert normalize_text(None) == ""  # type: ignore

    def test_already_normalized(self) -> None:
        """Test already normalized text."""
        assert normalize_text("hello world") == "hello world"


class TestTruncateText:
    """Tests for truncate_text function."""

    def test_no_truncation_needed(self) -> None:
        """Test text that doesn't need truncation."""
        assert truncate_text("hello", 10) == "hello"
        assert truncate_text("hello world", 20) == "hello world"

    def test_truncation_with_suffix(self) -> None:
        """Test truncation with default suffix."""
        result = truncate_text("hello world", 8)
        assert len(result) == 8
        assert result.endswith("...")
        assert result == "hello..."

    def test_truncation_custom_suffix(self) -> None:
        """Test truncation with custom suffix."""
        result = truncate_text("hello world", 8, suffix="…")
        assert len(result) == 8
        assert result.endswith("…")

    def test_empty_or_none(self) -> None:
        """Test empty or None text."""
        assert truncate_text("", 10) == ""
        assert truncate_text(None, 10) == ""  # type: ignore

    def test_zero_max_length(self) -> None:
        """Test zero max length."""
        assert truncate_text("hello", 0) == ""

    def test_negative_max_length(self) -> None:
        """Test negative max length."""
        assert truncate_text("hello", -1) == ""


class TestCleanText:
    """Tests for clean_text function."""

    def test_remove_control_characters(self) -> None:
        """Test removal of control characters."""
        text = "hello\x00world\x1f"
        assert clean_text(text) == "hello world"

    def test_normalize_whitespace(self) -> None:
        """Test normalization of whitespace."""
        assert clean_text("hello    world") == "hello world"
        assert clean_text("hello\t\tworld") == "hello world"

    def test_empty_or_none(self) -> None:
        """Test empty or None text."""
        assert clean_text("") == ""
        assert clean_text(None) == ""  # type: ignore

    def test_already_clean(self) -> None:
        """Test already clean text."""
        assert clean_text("hello world") == "hello world"


class TestExtractSentences:
    """Tests for extract_sentences function."""

    def test_extract_sentences(self) -> None:
        """Test sentence extraction."""
        text = "Hello world. How are you? I'm fine!"
        sentences = extract_sentences(text)
        assert len(sentences) == 3
        assert "Hello world" in sentences
        assert "How are you" in sentences
        assert "I'm fine" in sentences

    def test_empty_or_none(self) -> None:
        """Test empty or None text."""
        assert extract_sentences("") == []
        assert extract_sentences(None) == []  # type: ignore

    def test_no_sentences(self) -> None:
        """Test text without sentence-ending punctuation."""
        assert extract_sentences("hello world") == ["hello world"]

    def test_multiple_punctuation(self) -> None:
        """Test multiple sentence-ending punctuation."""
        text = "Hello!!! How are you??? I'm fine..."
        sentences = extract_sentences(text)
        assert len(sentences) == 3


class TestWordCount:
    """Tests for word_count function."""

    def test_word_count(self) -> None:
        """Test word counting."""
        assert word_count("hello world") == 2
        assert word_count("hello") == 1
        assert word_count("hello   world   test") == 3

    def test_empty_or_none(self) -> None:
        """Test empty or None text."""
        assert word_count("") == 0
        assert word_count(None) == 0  # type: ignore

    def test_multiple_spaces(self) -> None:
        """Test word count with multiple spaces."""
        assert word_count("hello    world") == 2


class TestCharCount:
    """Tests for char_count function."""

    def test_char_count_with_spaces(self) -> None:
        """Test character counting including spaces."""
        assert char_count("hello world") == 11
        assert char_count("hello") == 5

    def test_char_count_exclude_spaces(self) -> None:
        """Test character counting excluding spaces."""
        assert char_count("hello world", exclude_spaces=True) == 10
        assert char_count("hello   world", exclude_spaces=True) == 10

    def test_empty_or_none(self) -> None:
        """Test empty or None text."""
        assert char_count("") == 0
        assert char_count(None) == 0  # type: ignore
        assert char_count("", exclude_spaces=True) == 0
        assert char_count(None, exclude_spaces=True) == 0  # type: ignore

