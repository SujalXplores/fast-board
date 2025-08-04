"""
Custom exceptions for FastBoard application.
Provides specific error types for better error handling and debugging.
"""

from typing import Any, Dict, Optional


class FastBoardException(Exception):
    """Base exception class for FastBoard application."""
    
    def __init__(
        self,
        message: str,
        detail: Optional[str] = None,
        error_code: Optional[str] = None
    ) -> None:
        self.message = message
        self.detail = detail
        self.error_code = error_code
        super().__init__(self.message)


class WebSocketException(FastBoardException):
    """Exception raised for WebSocket-related errors."""
    pass


class AIServiceException(FastBoardException):
    """Exception raised for AI service-related errors."""
    pass


class ValidationException(FastBoardException):
    """Exception raised for data validation errors."""
    pass


class ConfigurationException(FastBoardException):
    """Exception raised for configuration-related errors."""
    pass


class RateLimitException(FastBoardException):
    """Exception raised when rate limits are exceeded."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        **kwargs
    ) -> None:
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class CanvasException(FastBoardException):
    """Exception raised for canvas-related errors."""
    pass
