"""
Pydantic models for FastBoard application.
Defines data structures and validation for WebSocket messages and API requests.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator


class MessageType(str, Enum):
    """Enumeration of WebSocket message types."""
    DRAW = "draw"
    TEXT = "text"
    CLEAR = "clear"
    CURSOR = "cursor"
    USER_COUNT = "user_count"
    BOARD_STATE = "board_state"
    ERROR = "error"


class ToolType(str, Enum):
    """Enumeration of drawing tool types."""
    PEN = "pen"
    ERASER = "eraser"


class Point(BaseModel):
    """Represents a point with x, y coordinates."""
    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate")
    
    @field_validator("x", "y")
    @classmethod
    def validate_coordinates(cls, v: float) -> float:
        """Validate coordinates are reasonable values."""
        if not -10000 <= v <= 10000:
            raise ValueError("Coordinate value out of reasonable range")
        return v


class DrawPayload(BaseModel):
    """Payload for drawing actions."""
    tool: ToolType = Field(..., description="Drawing tool type")
    color: str = Field(..., description="Color in hex format", pattern=r"^#[0-9A-Fa-f]{6}$")
    size: int = Field(..., description="Brush size", ge=1, le=100)
    points: List[Point] = Field(..., description="List of drawing points", min_length=1)
    
    @field_validator("points")
    @classmethod
    def validate_points_limit(cls, v: List[Point]) -> List[Point]:
        """Ensure points list doesn't exceed maximum length."""
        from app.core.config import settings
        if len(v) > settings.max_stroke_points:
            raise ValueError(f"Too many points in stroke (max: {settings.max_stroke_points})")
        return v


class TextPayload(BaseModel):
    """Payload for text actions."""
    content: str = Field(..., description="Text content", max_length=1000)
    x: float = Field(..., description="X position")
    y: float = Field(..., description="Y position")
    font: str = Field(default="16px Arial", description="Font specification")
    color: str = Field(..., description="Text color in hex format", pattern=r"^#[0-9A-Fa-f]{6}$")


class CursorPayload(BaseModel):
    """Payload for cursor position updates."""
    x: float = Field(..., description="Cursor X position")
    y: float = Field(..., description="Cursor Y position")


class UserCountPayload(BaseModel):
    """Payload for user count updates."""
    count: int = Field(..., description="Number of connected users", ge=0)


class BoardStatePayload(BaseModel):
    """Payload for board state synchronization."""
    actions: List[Dict[str, Any]] = Field(default_factory=list, description="List of board actions")


class ErrorPayload(BaseModel):
    """Payload for error messages."""
    message: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")


class WebSocketMessage(BaseModel):
    """Base WebSocket message structure."""
    type: MessageType = Field(..., description="Message type")
    client_id: str = Field(..., description="Client identifier", alias="clientId")
    payload: Optional[Union[
        DrawPayload,
        TextPayload,
        CursorPayload,
        UserCountPayload,
        BoardStatePayload,
        ErrorPayload,
        Dict[str, Any]
    ]] = Field(None, description="Message payload")
    
    model_config = {
        "populate_by_name": True,
        "use_enum_values": True
    }


class AIAssistRequest(BaseModel):
    """Request model for AI Assist endpoint."""
    image_data: str = Field(..., description="Base64 encoded canvas image data")
    
    @field_validator("image_data")
    @classmethod
    def validate_image_data(cls, v: str) -> str:
        """Validate image data format."""
        if not v.startswith("data:image/"):
            raise ValueError("Image data must be a valid data URL")
        return v


class AIAssistResponse(BaseModel):
    """Response model for AI Assist endpoint."""
    success: bool = Field(..., description="Whether the request was successful")
    interpretation: Optional[str] = Field(None, description="AI interpretation of the image")
    error: Optional[str] = Field(None, description="Error message if unsuccessful")


class ConnectionInfo(BaseModel):
    """Information about a WebSocket connection."""
    client_id: str = Field(..., description="Unique client identifier")
    connected_at: float = Field(..., description="Connection timestamp")
    last_activity: float = Field(..., description="Last activity timestamp")
    ip_address: Optional[str] = Field(None, description="Client IP address")
