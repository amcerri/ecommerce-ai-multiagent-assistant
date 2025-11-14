"""
Type extensions (JSON-compatible type definitions).

Overview
  Defines extended type definitions for JSON-compatible data structures.
  These types provide type safety for functions that work with JSON data
  serialization and deserialization.

Design
  - **JSON Compatibility**: Types represent values that can be serialized to JSON.
  - **Type Safety**: Provides type hints for JSON data structures.
  - **Recursive Types**: Supports nested JSON structures (dicts and lists).

Integration
  - Consumes: None (pure type definitions).
  - Returns: Type definitions for use in type annotations.
  - Used by: All modules that work with JSON data.
  - Observability: N/A (types only).

Usage
  >>> from app.utils.typing_ext import JSONValue, JSONDict, JSONList
  >>> def process_json(data: JSONDict) -> JSONList:
  ...     return []
"""

from typing import Any, Union

# JSON-compatible value types
JSONValue = Union[str, int, float, bool, None, dict[str, Any], list[Any]]

# JSON-compatible dictionary (string keys, JSON-compatible values)
JSONDict = dict[str, JSONValue]

# JSON-compatible list (JSON-compatible values)
JSONList = list[JSONValue]

