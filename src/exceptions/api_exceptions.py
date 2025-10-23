from typing import Any


class BaseAPIError(Exception):
    """Base exception for all API exceptions."""

    def __init__(self, message: str, details: Any = None):
        self.message = message
        self.details = details
        super().__init__(self.message)


class DatabaseError(BaseAPIError):
    """Exception raised for database related errors."""

    pass


class NotFoundError(BaseAPIError):
    """Exception raised when a resource is not found."""

    pass


class ValidationError(BaseAPIError):
    """Exception raised for validation errors."""

    pass


class AuthenticationError(BaseAPIError):
    """Exception raised for authentication related errors."""

    pass


class PermissionError(BaseAPIError):
    """Exception raised for permission related errors."""

    pass
