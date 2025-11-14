"""
Date utilities (datetime manipulation and formatting functions).

Overview
  Provides utility functions for parsing, formatting, and manipulating
  datetime objects. All functions work with timezone-aware datetimes
  using zoneinfo (Python 3.9+ built-in) and python-dateutil for flexible parsing.

Design
  - **Timezone-Aware**: All datetimes are timezone-aware (UTC by default).
  - **Zoneinfo**: Uses zoneinfo (built-in) instead of pytz.
  - **Dateutil**: Uses python-dateutil for flexible date parsing.
  - **Type Safety**: All functions use type hints for parameters and return values.

Integration
  - Consumes: datetime, zoneinfo (stdlib), dateutil.parser.
  - Returns: datetime objects or formatted strings.
  - Used by: All modules that need date/time manipulation.
  - Observability: N/A (pure date manipulation functions).

Usage
  >>> from app.utils.date import parse_date, format_date, get_timezone_aware_now
  >>> dt = parse_date("2024-01-01")
  >>> formatted = format_date(dt)
  >>> now = get_timezone_aware_now()
"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from dateutil import parser as dateutil_parser


def parse_date(date_string: str, format: str | None = None) -> datetime:
    """Parse date string to timezone-aware datetime.

    Parses date string to datetime object. If format is provided, uses
    strptime. Otherwise, uses dateutil.parser for flexible parsing.
    Always returns timezone-aware datetime (UTC if timezone not specified).

    Args:
        date_string: Date string to parse.
        format: Optional format string for strptime parsing.

    Returns:
        Timezone-aware datetime object (UTC if timezone not in string).

    Raises:
        ValueError: If date string cannot be parsed.
    """
    if not date_string or not isinstance(date_string, str):
        raise ValueError("date_string must be a non-empty string")

    if format:
        dt = datetime.strptime(date_string, format)
    else:
        dt = dateutil_parser.parse(date_string)

    # Ensure timezone-aware (default to UTC if naive)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt


def format_date(dt: datetime, format: str = "%Y-%m-%d") -> str:
    """Format datetime to string.

    Formats datetime object to string using specified format.
    If datetime is naive, assumes UTC timezone.

    Args:
        dt: Datetime object to format.
        format: Format string (default: "%Y-%m-%d").

    Returns:
        Formatted date string.

    Raises:
        ValueError: If datetime is invalid.
    """
    if not isinstance(dt, datetime):
        raise ValueError("dt must be a datetime object")

    # Ensure timezone-aware (default to UTC if naive)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.strftime(format)


def format_date_relative(dt: datetime, locale: str = "pt-BR") -> str:
    """Format datetime as relative time string.

    Formats datetime as relative time (e.g., "há 2 dias", "em 3 horas").
    Supports multiple locales (pt-BR, en-US, etc.).

    Args:
        dt: Datetime object to format.
        locale: Locale for translation (default: "pt-BR").

    Returns:
        Relative time string. Returns "data inválida" if datetime is invalid.
    """
    if not isinstance(dt, datetime):
        return "data inválida"

    try:
        # Ensure timezone-aware (default to UTC if naive)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        delta = dt - now
        total_seconds = int(delta.total_seconds())
        abs_seconds = abs(total_seconds)

        # Define translations for different locales
        translations = {
            "pt-BR": {
                "past": {
                    "second": "há {n} segundo",
                    "seconds": "há {n} segundos",
                    "minute": "há {n} minuto",
                    "minutes": "há {n} minutos",
                    "hour": "há {n} hora",
                    "hours": "há {n} horas",
                    "day": "há {n} dia",
                    "days": "há {n} dias",
                    "week": "há {n} semana",
                    "weeks": "há {n} semanas",
                    "month": "há {n} mês",
                    "months": "há {n} meses",
                    "year": "há {n} ano",
                    "years": "há {n} anos",
                },
                "future": {
                    "second": "em {n} segundo",
                    "seconds": "em {n} segundos",
                    "minute": "em {n} minuto",
                    "minutes": "em {n} minutos",
                    "hour": "em {n} hora",
                    "hours": "em {n} horas",
                    "day": "em {n} dia",
                    "days": "em {n} dias",
                    "week": "em {n} semana",
                    "weeks": "em {n} semanas",
                    "month": "em {n} mês",
                    "months": "em {n} meses",
                    "year": "em {n} ano",
                    "years": "em {n} anos",
                },
            },
            "en-US": {
                "past": {
                    "second": "{n} second ago",
                    "seconds": "{n} seconds ago",
                    "minute": "{n} minute ago",
                    "minutes": "{n} minutes ago",
                    "hour": "{n} hour ago",
                    "hours": "{n} hours ago",
                    "day": "{n} day ago",
                    "days": "{n} days ago",
                    "week": "{n} week ago",
                    "weeks": "{n} weeks ago",
                    "month": "{n} month ago",
                    "months": "{n} months ago",
                    "year": "{n} year ago",
                    "years": "{n} years ago",
                },
                "future": {
                    "second": "in {n} second",
                    "seconds": "in {n} seconds",
                    "minute": "in {n} minute",
                    "minutes": "in {n} minutes",
                    "hour": "in {n} hour",
                    "hours": "in {n} hours",
                    "day": "in {n} day",
                    "days": "in {n} days",
                    "week": "in {n} week",
                    "weeks": "in {n} weeks",
                    "month": "in {n} month",
                    "months": "in {n} months",
                    "year": "in {n} year",
                    "years": "in {n} years",
                },
            },
        }

        # Get translations for locale (default to pt-BR)
        locale_translations = translations.get(locale, translations["pt-BR"])
        direction = "past" if total_seconds < 0 else "future"
        trans = locale_translations[direction]

        # Calculate time units
        if abs_seconds < 60:
            unit = "second" if abs_seconds == 1 else "seconds"
            return trans[unit].format(n=abs_seconds)
        elif abs_seconds < 3600:
            n = abs_seconds // 60
            unit = "minute" if n == 1 else "minutes"
            return trans[unit].format(n=n)
        elif abs_seconds < 86400:
            n = abs_seconds // 3600
            unit = "hour" if n == 1 else "hours"
            return trans[unit].format(n=n)
        elif abs_seconds < 604800:
            n = abs_seconds // 86400
            unit = "day" if n == 1 else "days"
            return trans[unit].format(n=n)
        elif abs_seconds < 2592000:
            n = abs_seconds // 604800
            unit = "week" if n == 1 else "weeks"
            return trans[unit].format(n=n)
        elif abs_seconds < 31536000:
            n = abs_seconds // 2592000
            unit = "month" if n == 1 else "months"
            return trans[unit].format(n=n)
        else:
            n = abs_seconds // 31536000
            unit = "year" if n == 1 else "years"
            return trans[unit].format(n=n)

    except Exception:
        return "data inválida"


def is_valid_date(date_string: str) -> bool:
    """Validate if string is a valid date.

    Attempts to parse date string and returns True if parsing succeeds.

    Args:
        date_string: Date string to validate.

    Returns:
        True if date string is valid, False otherwise.
    """
    if not date_string or not isinstance(date_string, str):
        return False

    try:
        parse_date(date_string)
        return True
    except (ValueError, TypeError):
        return False


def get_timezone_aware_now() -> datetime:
    """Get current timezone-aware datetime in UTC.

    Returns current datetime with UTC timezone.

    Returns:
        Current datetime with UTC timezone.
    """
    return datetime.now(timezone.utc)


def to_utc(dt: datetime) -> datetime:
    """Convert datetime to UTC timezone.

    Converts datetime to UTC timezone. If datetime already has timezone,
    converts it. If datetime is naive, assumes it's already in UTC and
    adds UTC timezone.

    Args:
        dt: Datetime object to convert.

    Returns:
        Datetime object in UTC timezone.

    Raises:
        ValueError: If datetime is invalid.
    """
    if not isinstance(dt, datetime):
        raise ValueError("dt must be a datetime object")

    if dt.tzinfo is None:
        # Assume naive datetime is in UTC
        return dt.replace(tzinfo=timezone.utc)

    # Convert to UTC
    return dt.astimezone(timezone.utc)

