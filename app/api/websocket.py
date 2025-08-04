"""
WebSocket endpoints for real-time collaboration.
Handles WebSocket connections and message processing.
"""

import json
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends

from app.core.exceptions import WebSocketException, ValidationException
from app.core.logging import get_logger
from app.models.schemas import WebSocketMessage, MessageType
from app.services.connection_manager import ConnectionManager
from app.utils.helpers import get_client_ip, safe_json_loads

logger = get_logger("websocket_endpoints")

router = APIRouter()


def get_connection_manager() -> ConnectionManager:
    """Dependency to get the connection manager instance."""
    return connection_manager


# Global connection manager instance
connection_manager = ConnectionManager()


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str,
    manager: ConnectionManager = Depends(get_connection_manager)
) -> None:
    """
    Handle WebSocket connections for real-time collaboration.
    
    Args:
        websocket: The WebSocket connection
        client_id: Unique identifier for the client
        manager: Connection manager instance
    """
    # Get client IP for logging and security
    client_ip = None
    if hasattr(websocket, "headers"):
        # Extract IP from headers if available
        forwarded_for = websocket.headers.get("x-forwarded-for")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
    
    try:
        # Accept the connection
        await manager.connect(websocket, client_id, client_ip)
        
        # Main message handling loop
        while True:
            try:
                # Receive message from client
                raw_data = await websocket.receive_text()
                
                # Parse and validate the message
                message = await _process_incoming_message(raw_data, client_id, manager)
                
                if message:
                    # Broadcast the validated message to other clients
                    await manager.broadcast(message, exclude_client=client_id)
                    
                    logger.debug(f"Processed {message.type} from client {client_id}")
            
            except WebSocketDisconnect:
                logger.info(f"Client {client_id} disconnected normally")
                break
            
            except ValidationException as e:
                logger.warning(f"Validation error from client {client_id}: {e.message}")
                await _send_error_message(websocket, e.message, "VALIDATION_ERROR")
            
            except Exception as e:
                logger.error(f"Error processing message from client {client_id}: {e}")
                await _send_error_message(websocket, "Message processing failed", "PROCESSING_ERROR")
    
    except WebSocketException as e:
        logger.error(f"WebSocket error for client {client_id}: {e.message}")
    
    except Exception as e:
        logger.error(f"Unexpected error in WebSocket handler for client {client_id}: {e}")
    
    finally:
        # Clean up the connection
        await manager.disconnect(client_id)


async def _process_incoming_message(
    raw_data: str,
    client_id: str,
    manager: ConnectionManager
) -> Optional[WebSocketMessage]:
    """
    Process and validate incoming WebSocket message.
    
    Args:
        raw_data: Raw message data from client
        client_id: Client identifier
        manager: Connection manager instance
    
    Returns:
        Validated WebSocket message or None if invalid
    
    Raises:
        ValidationException: If message validation fails
    """
    # Parse JSON
    message_data = safe_json_loads(raw_data)
    if message_data is None:
        raise ValidationException("Invalid JSON format")
    
    # Validate required fields
    if not isinstance(message_data, dict):
        raise ValidationException("Message must be a JSON object")
    
    if "type" not in message_data:
        raise ValidationException("Message type is required")
    
    if "clientId" not in message_data:
        raise ValidationException("Client ID is required")
    
    # Verify client ID matches
    if message_data["clientId"] != client_id:
        raise ValidationException("Client ID mismatch")
    
    try:
        # Create and validate the message using Pydantic
        message = WebSocketMessage(**message_data)
        
        # Handle persistent actions (add to board state)
        if message.type in [MessageType.DRAW, MessageType.TEXT]:
            manager.add_to_board_state(message_data)
        elif message.type == MessageType.CLEAR:
            manager.add_to_board_state(message_data)
        
        return message
    
    except ValueError as e:
        raise ValidationException(f"Message validation failed: {str(e)}")


async def _send_error_message(websocket: WebSocket, message: str, error_code: str) -> None:
    """
    Send an error message to the client.
    
    Args:
        websocket: WebSocket connection
        message: Error message
        error_code: Error code identifier
    """
    try:
        error_message = WebSocketMessage(
            type=MessageType.ERROR,
            client_id="server",
            payload={
                "message": message,
                "code": error_code
            }
        )
        await websocket.send_text(error_message.json())
    except Exception as e:
        logger.error(f"Failed to send error message: {e}")


@router.get("/ws/stats")
async def get_websocket_stats(manager: ConnectionManager = Depends(get_connection_manager)) -> dict:
    """
    Get WebSocket connection statistics.
    
    Args:
        manager: Connection manager instance
    
    Returns:
        Dictionary containing connection statistics
    """
    connections_info = manager.get_all_connection_info()
    
    return {
        "total_connections": manager.active_connections_count,
        "connections": [
            {
                "client_id": info.client_id,
                "connected_at": info.connected_at,
                "last_activity": info.last_activity,
                "ip_address": info.ip_address,
                "session_duration": info.last_activity - info.connected_at
            }
            for info in connections_info
        ]
    }
