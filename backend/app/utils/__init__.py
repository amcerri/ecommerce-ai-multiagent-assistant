"""
Utility functions module (validation, types, text, date).

Overview
  Centralized utility functions module providing validation, type extensions,
  text processing, and date manipulation functionality. All utility functions
  are pure (no side effects) for easy testing and reuse.

Design
  - **Pure Functions**: All utility functions are pure (no side effects).
  - **Type Safety**: All functions use type hints for parameters and return values.
  - **Explicit Exports**: __all__ defines all public exports.
  - **Organized**: Exports organized by category (validation, types, text, date).

Integration
  - Consumes: app.config.constants, app.config.exceptions, datetime, zoneinfo, dateutil.
  - Returns: Validation results, processed text, datetime objects, type definitions.
  - Used by: All application modules that need utility functions.
  - Observability: N/A (pure utility functions).

Usage
  >>> from app.utils import validate_email, normalize_text, parse_date, JSONDict
  >>> is_valid = validate_email("user@example.com")
  >>> normalized = normalize_text("  Hello   World  ")
  >>> dt = parse_date("2024-01-01")
"""

# Validation
from app.utils.validation import (
    validate_email,
    validate_file,
    validate_file_size,
    validate_file_type,
    validate_url,
)

# Type Extensions
from app.utils.typing_ext import JSONDict, JSONList, JSONValue

# Text Processing
from app.utils.text import (
    char_count,
    clean_text,
    extract_sentences,
    normalize_text,
    truncate_text,
    word_count,
)

# Date Utilities
from app.utils.date import (
    format_date,
    format_date_relative,
    get_timezone_aware_now,
    is_valid_date,
    parse_date,
    to_utc,
)

__all__ = [
    # Validation
    "validate_email",
    "validate_url",
    "validate_file_type",
    "validate_file_size",
    "validate_file",
    # Type Extensions
    "JSONValue",
    "JSONDict",
    "JSONList",
    # Text Processing
    "normalize_text",
    "truncate_text",
    "clean_text",
    "extract_sentences",
    "word_count",
    "char_count",
    # Date Utilities
    "parse_date",
    "format_date",
    "format_date_relative",
    "is_valid_date",
    "get_timezone_aware_now",
    "to_utc",
]

