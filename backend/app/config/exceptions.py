"""
Custom exception hierarchy (structured error handling).

Overview
  Defines hierarchical exception classes for structured error handling throughout
  the application. Exceptions are categorized by type (system, business, user) and
  include HTTP status codes for API error responses.

Design
  - **Hierarchical Structure**: AppBaseException as base, with specialized subclasses.
  - **HTTP Status Codes**: Each exception includes appropriate HTTP status code.
  - **Error Details**: Optional details dict for additional context.
  - **Type Safety**: All exceptions use type hints for message, details, and status_code.
  - **Naming**: Uses AppBaseException (not BaseException) to avoid conflict with built-in.

Integration
  - Consumes: None (base exception classes).
  - Returns: Exception instances with structured error information.
  - Used by: All application modules for error handling.
  - Observability: Exceptions include details for logging and tracing.

Usage
  >>> from app.config.exceptions import DatabaseException, ValidationException
  >>> raise DatabaseException("Connection failed", details={"host": "localhost"})
  >>> raise ValidationException("Invalid input", status_code=400)
"""


class AppBaseException(Exception):
    """Base exception for all custom application exceptions.

    Provides structured error handling with message, optional details,
    and HTTP status code. All custom exceptions inherit from this class.

    Attributes:
        message: Error message describing what went wrong.
        details: Optional dictionary with additional error context.
        status_code: HTTP status code for API responses (default: 500).

    Args:
        message: Error message.
        details: Optional error details dictionary.
        status_code: HTTP status code (default: 500).
    """

    def __init__(
        self,
        message: str,
        details: dict | None = None,
        status_code: int = 500,
    ) -> None:
        """Initialize base exception.

        Args:
            message: Error message.
            details: Optional error details dictionary.
            status_code: HTTP status code (default: 500).
        """
        super().__init__(message)
        self.message = message
        self.details = details
        self.status_code = status_code


class SystemException(AppBaseException):
    """Exception for system-level errors.

    Represents errors in infrastructure, external services, or system components.
    Default status code is 500 (Internal Server Error).

    Args:
        message: Error message.
        details: Optional error details dictionary.
        status_code: HTTP status code (default: 500).
    """

    def __init__(
        self,
        message: str,
        details: dict | None = None,
        status_code: int = 500,
    ) -> None:
        """Initialize system exception.

        Args:
            message: Error message.
            details: Optional error details dictionary.
            status_code: HTTP status code (default: 500).
        """
        super().__init__(message, details, status_code)


class BusinessException(AppBaseException):
    """Exception for business logic errors.

    Represents errors in business rules, validation, or application logic.
    Default status code is 400 (Bad Request).

    Args:
        message: Error message.
        details: Optional error details dictionary.
        status_code: HTTP status code (default: 400).
    """

    def __init__(
        self,
        message: str,
        details: dict | None = None,
        status_code: int = 400,
    ) -> None:
        """Initialize business exception.

        Args:
            message: Error message.
            details: Optional error details dictionary.
            status_code: HTTP status code (default: 400).
        """
        super().__init__(message, details, status_code)


class UserException(AppBaseException):
    """Exception for user-facing errors.

    Represents errors that users can correct, such as invalid input or rate limits.
    Default status code is 400 (Bad Request).

    Args:
        message: Error message.
        details: Optional error details dictionary.
        status_code: HTTP status code (default: 400).
    """

    def __init__(
        self,
        message: str,
        details: dict | None = None,
        status_code: int = 400,
    ) -> None:
        """Initialize user exception.

        Args:
            message: Error message.
            details: Optional error details dictionary.
            status_code: HTTP status code (default: 400).
        """
        super().__init__(message, details, status_code)


# System Exception Subclasses
class DatabaseException(SystemException):
    """Exception for database-related errors.

    Represents errors in database operations, connections, or queries.
    Status code: 500 (Internal Server Error).

    Args:
        message: Error message.
        details: Optional error details dictionary.
    """

    def __init__(
        self,
        message: str,
        details: dict | None = None,
    ) -> None:
        """Initialize database exception.

        Args:
            message: Error message.
            details: Optional error details dictionary.
        """
        super().__init__(message, details, status_code=500)


class LLMException(SystemException):
    """Exception for LLM API errors.

    Represents errors in LLM API calls, timeouts, or API failures.
    Status code: 502 (Bad Gateway).

    Args:
        message: Error message.
        details: Optional error details dictionary.
    """

    def __init__(
        self,
        message: str,
        details: dict | None = None,
    ) -> None:
        """Initialize LLM exception.

        Args:
            message: Error message.
            details: Optional error details dictionary.
        """
        super().__init__(message, details, status_code=502)


class StorageException(SystemException):
    """Exception for storage-related errors.

    Represents errors in file storage, local storage, or storage operations.
    Status code: 500 (Internal Server Error).

    Args:
        message: Error message.
        details: Optional error details dictionary.
    """

    def __init__(
        self,
        message: str,
        details: dict | None = None,
    ) -> None:
        """Initialize storage exception.

        Args:
            message: Error message.
            details: Optional error details dictionary.
        """
        super().__init__(message, details, status_code=500)


# Business Exception Subclasses
class ValidationException(BusinessException):
    """Exception for validation errors.

    Represents errors in data validation or business rule validation.
    Status code: 400 (Bad Request).

    Args:
        message: Error message.
        details: Optional error details dictionary.
    """

    def __init__(
        self,
        message: str,
        details: dict | None = None,
    ) -> None:
        """Initialize validation exception.

        Args:
            message: Error message.
            details: Optional error details dictionary.
        """
        super().__init__(message, details, status_code=400)


class AuthorizationException(BusinessException):
    """Exception for authorization errors.

    Represents errors when user lacks permission to perform action.
    Status code: 403 (Forbidden).

    Args:
        message: Error message.
        details: Optional error details dictionary.
    """

    def __init__(
        self,
        message: str,
        details: dict | None = None,
    ) -> None:
        """Initialize authorization exception.

        Args:
            message: Error message.
            details: Optional error details dictionary.
        """
        super().__init__(message, details, status_code=403)


class NotFoundException(BusinessException):
    """Exception for resource not found errors.

    Represents errors when requested resource does not exist.
    Status code: 404 (Not Found).

    Args:
        message: Error message.
        details: Optional error details dictionary.
    """

    def __init__(
        self,
        message: str,
        details: dict | None = None,
    ) -> None:
        """Initialize not found exception.

        Args:
            message: Error message.
            details: Optional error details dictionary.
        """
        super().__init__(message, details, status_code=404)


# User Exception Subclasses
class InvalidInputException(UserException):
    """Exception for invalid user input.

    Represents errors when user provides invalid or malformed input.
    Status code: 400 (Bad Request).

    Args:
        message: Error message.
        details: Optional error details dictionary.
    """

    def __init__(
        self,
        message: str,
        details: dict | None = None,
    ) -> None:
        """Initialize invalid input exception.

        Args:
            message: Error message.
            details: Optional error details dictionary.
        """
        super().__init__(message, details, status_code=400)


class RateLimitException(UserException):
    """Exception for rate limit exceeded.

    Represents errors when user exceeds rate limits.
    Status code: 429 (Too Many Requests).

    Args:
        message: Error message.
        details: Optional error details dictionary.
    """

    def __init__(
        self,
        message: str,
        details: dict | None = None,
    ) -> None:
        """Initialize rate limit exception.

        Args:
            message: Error message.
            details: Optional error details dictionary.
        """
        super().__init__(message, details, status_code=429)

