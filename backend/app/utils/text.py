"""
Text processing utilities (text manipulation functions).

Overview
  Provides utility functions for text processing including normalization,
  truncation, cleaning, sentence extraction, and word/character counting.
  All functions are pure (no side effects) for easy testing and reuse.

Design
  - **Pure Functions**: All functions are pure (no side effects).
  - **Error Handling**: Handles None and empty strings gracefully.
  - **Performance**: Uses built-in Python methods for optimal performance.
  - **Type Safety**: All functions use type hints for parameters and return values.

Integration
  - Consumes: None (pure text processing).
  - Returns: Processed text or counts.
  - Used by: All modules that need text processing functionality.
  - Observability: N/A (pure text processing functions).

Usage
  >>> from app.utils.text import normalize_text, truncate_text, word_count
  >>> normalized = normalize_text("  Hello   World  ")
  >>> truncated = truncate_text("Long text", max_length=5)
  >>> count = word_count("Hello world")
"""

import re


def normalize_text(text: str) -> str:
    """Normalize text by removing extra spaces and normalizing line breaks.

    Removes multiple consecutive spaces, normalizes line breaks to single
    newline character, and strips leading/trailing whitespace.

    Args:
        text: Text string to normalize.

    Returns:
        Normalized text string. Returns empty string if text is None.
    """
    if not text or not isinstance(text, str):
        return ""

    # Remove multiple spaces
    normalized = re.sub(r" +", " ", text)
    # Normalize line breaks
    normalized = re.sub(r"\r\n|\r", "\n", normalized)
    # Remove multiple newlines
    normalized = re.sub(r"\n+", "\n", normalized)
    # Strip leading/trailing whitespace
    return normalized.strip()


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to maximum length with optional suffix.

    Truncates text to max_length characters, adding suffix if truncation
    occurred. Suffix length is considered in truncation calculation.

    Args:
        text: Text string to truncate.
        max_length: Maximum length of result (including suffix if added).
        suffix: Suffix to add if truncation occurs (default: "...").

    Returns:
        Truncated text with suffix if needed. Returns empty string if
        text is None or max_length <= 0.
    """
    if not text or not isinstance(text, str):
        return ""
    if max_length <= 0:
        return ""

    if len(text) <= max_length:
        return text

    # Calculate truncation length considering suffix
    truncate_length = max_length - len(suffix)
    if truncate_length <= 0:
        return suffix[:max_length]

    return text[:truncate_length] + suffix


def clean_text(text: str) -> str:
    """Clean text by removing control characters and normalizing whitespace.

    Removes control characters (non-printable), normalizes whitespace
    to single spaces, and strips leading/trailing whitespace.

    Args:
        text: Text string to clean.

    Returns:
        Cleaned text string. Returns empty string if text is None.
    """
    if not text or not isinstance(text, str):
        return ""

    # Remove control characters (keep printable characters and whitespace)
    cleaned = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", text)
    # Normalize whitespace
    cleaned = re.sub(r"\s+", " ", cleaned)
    # Strip leading/trailing whitespace
    return cleaned.strip()


def extract_sentences(text: str) -> list[str]:
    """Extract sentences from text.

    Splits text into sentences using sentence-ending punctuation (. ! ?),
    removes extra whitespace from each sentence, and filters empty sentences.

    Args:
        text: Text string to extract sentences from.

    Returns:
        List of sentence strings. Returns empty list if text is None or empty.
    """
    if not text or not isinstance(text, str):
        return []

    # Split by sentence-ending punctuation
    sentences = re.split(r"[.!?]+", text)
    # Clean and filter sentences
    result = []
    for sentence in sentences:
        cleaned = sentence.strip()
        if cleaned:
            result.append(cleaned)

    return result


def word_count(text: str) -> int:
    """Count words in text.

    Splits text by whitespace and counts non-empty words.

    Args:
        text: Text string to count words in.

    Returns:
        Number of words. Returns 0 if text is None or empty.
    """
    if not text or not isinstance(text, str):
        return 0

    words = text.split()
    return len([word for word in words if word.strip()])


def char_count(text: str, exclude_spaces: bool = False) -> int:
    """Count characters in text.

    Counts characters in text, optionally excluding spaces.

    Args:
        text: Text string to count characters in.
        exclude_spaces: If True, exclude spaces from count (default: False).

    Returns:
        Number of characters. Returns 0 if text is None.
    """
    if not text or not isinstance(text, str):
        return 0

    if exclude_spaces:
        return len(text.replace(" ", ""))
    return len(text)

