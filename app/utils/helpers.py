"""
Utility functions for FastBoard application.
Common helper functions used across the application.
"""

import re
import uuid
import time
from typing import Any, Dict, Optional
from fastapi import Request

from app.core.logging import get_logger

logger = get_logger("utils")


def generate_client_id() -> str:
    """
    Generate a unique client identifier.
    
    Returns:
        A unique client ID string
    """
    timestamp = str(int(time.time() * 1000))
    unique_id = str(uuid.uuid4()).replace("-", "")[:8]
    return f"client_{timestamp}_{unique_id}"


def validate_hex_color(color: str) -> bool:
    """
    Validate if a string is a valid hex color.
    
    Args:
        color: Color string to validate
    
    Returns:
        True if valid hex color, False otherwise
    """
    hex_pattern = re.compile(r"^#[0-9A-Fa-f]{6}$")
    return bool(hex_pattern.match(color))


def sanitize_text_content(content: str, max_length: int = 1000) -> str:
    """
    Sanitize text content for safety and length.
    
    Args:
        content: Text content to sanitize
        max_length: Maximum allowed length
    
    Returns:
        Sanitized text content
    """
    if not isinstance(content, str):
        return ""
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\']', '', content)
    
    # Trim to maximum length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    # Remove excessive whitespace
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    
    return sanitized


def get_client_ip(request: Request) -> Optional[str]:
    """
    Extract client IP address from request.
    
    Args:
        request: FastAPI request object
    
    Returns:
        Client IP address or None if not available
    """
    # Check for forwarded headers first (for reverse proxies)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs, take the first one
        return forwarded_for.split(",")[0].strip()
    
    # Check for real IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    
    # Fall back to direct client IP
    if hasattr(request, "client") and request.client:
        return request.client.host
    
    return None


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
    
    Returns:
        Formatted size string
    """
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate a string to a maximum length with suffix.
    
    Args:
        text: Text to truncate
        max_length: Maximum length before truncation
        suffix: Suffix to add when truncating
    
    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """
    Safely load JSON string with error handling.
    
    Args:
        json_str: JSON string to parse
        default: Default value to return on error
    
    Returns:
        Parsed JSON object or default value
    """
    try:
        import json
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"Failed to parse JSON: {e}")
        return default


def validate_canvas_dimensions(width: int, height: int, max_size: int = 4096) -> bool:
    """
    Validate canvas dimensions are within reasonable limits.
    
    Args:
        width: Canvas width
        height: Canvas height
        max_size: Maximum allowed dimension
    
    Returns:
        True if dimensions are valid, False otherwise
    """
    return (
        isinstance(width, int) and
        isinstance(height, int) and
        0 < width <= max_size and
        0 < height <= max_size
    )


def calculate_session_duration(start_time: float, end_time: Optional[float] = None) -> float:
    """
    Calculate session duration in seconds.
    
    Args:
        start_time: Session start timestamp
        end_time: Session end timestamp (current time if None)
    
    Returns:
        Duration in seconds
    """
    if end_time is None:
        end_time = time.time()
    
    return max(0, end_time - start_time)


def mask_sensitive_data(data: str, mask_char: str = "*", visible_chars: int = 4) -> str:
    """
    Mask sensitive data for logging purposes.
    
    Args:
        data: Data to mask
        mask_char: Character to use for masking
        visible_chars: Number of characters to keep visible at the end
    
    Returns:
        Masked string
    """
    if not data or len(data) <= visible_chars:
        return mask_char * len(data) if data else ""
    
    return mask_char * (len(data) - visible_chars) + data[-visible_chars:]


class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests per window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = {}
    
    def is_allowed(self, identifier: str) -> bool:
        """
        Check if request is allowed for the given identifier.
        
        Args:
            identifier: Unique identifier (e.g., IP address, client ID)
        
        Returns:
            True if request is allowed, False otherwise
        """
        current_time = time.time()
        
        # Initialize or get existing request history
        if identifier not in self.requests:
            self.requests[identifier] = []
        
        request_history = self.requests[identifier]
        
        # Remove old requests outside the time window
        cutoff_time = current_time - self.window_seconds
        self.requests[identifier] = [
            req_time for req_time in request_history 
            if req_time > cutoff_time
        ]
        
        # Check if under rate limit
        if len(self.requests[identifier]) < self.max_requests:
            self.requests[identifier].append(current_time)
            return True
        
        return False
    
    def cleanup_old_entries(self) -> None:
        """Clean up old entries to prevent memory leaks."""
        current_time = time.time()
        cutoff_time = current_time - (self.window_seconds * 2)  # Clean entries older than 2x window
        
        identifiers_to_remove = []
        for identifier, request_history in self.requests.items():
            # Remove old requests
            self.requests[identifier] = [
                req_time for req_time in request_history 
                if req_time > cutoff_time
            ]
            
            # Mark empty histories for removal
            if not self.requests[identifier]:
                identifiers_to_remove.append(identifier)
        
        # Remove empty histories
        for identifier in identifiers_to_remove:
            del self.requests[identifier]
