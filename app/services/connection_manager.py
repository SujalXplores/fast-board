"""
WebSocket connection manager for real-time collaboration.
Handles client connections, message broadcasting, and board state management.
"""

import json
import time
from typing import Any, Dict, List, Optional
from fastapi import WebSocket
from collections import defaultdict

from app.core.exceptions import WebSocketException
from app.core.logging import get_logger
from app.models.schemas import WebSocketMessage, MessageType, ConnectionInfo

logger = get_logger("connection_manager")


class ConnectionManager:
    """Manages WebSocket connections for real-time collaboration."""
    
    def __init__(self) -> None:
        """Initialize the connection manager."""
        self._active_connections: Dict[str, WebSocket] = {}
        self._connection_info: Dict[str, ConnectionInfo] = {}
        self._board_state: List[Dict[str, Any]] = []
        self._client_activity: Dict[str, float] = defaultdict(float)
    
    @property
    def active_connections_count(self) -> int:
        """Get the number of active connections."""
        return len(self._active_connections)
    
    @property
    def board_state(self) -> List[Dict[str, Any]]:
        """Get the current board state."""
        return self._board_state.copy()
    
    async def connect(self, websocket: WebSocket, client_id: str, ip_address: Optional[str] = None) -> None:
        """
        Accept a new WebSocket connection.
        
        Args:
            websocket: The WebSocket connection
            client_id: Unique identifier for the client
            ip_address: Optional IP address of the client
        
        Raises:
            WebSocketException: If connection setup fails
        """
        try:
            await websocket.accept()
            
            current_time = time.time()
            self._active_connections[client_id] = websocket
            self._connection_info[client_id] = ConnectionInfo(
                client_id=client_id,
                connected_at=current_time,
                last_activity=current_time,
                ip_address=ip_address
            )
            self._client_activity[client_id] = current_time
            
            logger.info(
                f"Client {client_id} connected from {ip_address or 'unknown'}. "
                f"Total connections: {self.active_connections_count}"
            )
            
            # Send current board state to new client
            if self._board_state:
                await self._send_board_state(websocket)
            
            # Broadcast user count update
            await self.broadcast_user_count()
            
        except Exception as e:
            logger.error(f"Failed to connect client {client_id}: {e}")
            raise WebSocketException(f"Connection failed: {str(e)}")
    
    async def disconnect(self, client_id: str) -> None:
        """
        Remove a WebSocket connection.
        
        Args:
            client_id: Unique identifier for the client to disconnect
        """
        if client_id in self._active_connections:
            del self._active_connections[client_id]
        
        if client_id in self._connection_info:
            connection_info = self._connection_info[client_id]
            session_duration = time.time() - connection_info.connected_at
            del self._connection_info[client_id]
            
            logger.info(
                f"Client {client_id} disconnected after {session_duration:.1f}s. "
                f"Total connections: {self.active_connections_count}"
            )
        
        if client_id in self._client_activity:
            del self._client_activity[client_id]
        
        # Broadcast updated user count after disconnect
        await self.broadcast_user_count()
    
    async def send_personal_message(self, message: WebSocketMessage, client_id: str) -> bool:
        """
        Send a message to a specific client.
        
        Args:
            message: The WebSocket message to send
            client_id: Target client identifier
        
        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        if client_id not in self._active_connections:
            logger.warning(f"Attempted to send message to non-existent client: {client_id}")
            return False
        
        try:
            websocket = self._active_connections[client_id]
            message_str = message.json() if isinstance(message, WebSocketMessage) else json.dumps(message)
            await websocket.send_text(message_str)
            self._update_client_activity(client_id)
            return True
        except Exception as e:
            logger.error(f"Error sending message to client {client_id}: {e}")
            await self._handle_connection_error(client_id)
            return False
    
    async def broadcast(self, message: WebSocketMessage, exclude_client: Optional[str] = None) -> int:
        """
        Broadcast a message to all connected clients.
        
        Args:
            message: The WebSocket message to broadcast
            exclude_client: Optional client ID to exclude from broadcast
        
        Returns:
            int: Number of clients that successfully received the message
        """
        if not self._active_connections:
            return 0
        
        message_str = message.json() if isinstance(message, WebSocketMessage) else json.dumps(message)
        successful_sends = 0
        failed_clients = []
        
        for client_id, websocket in self._active_connections.items():
            if exclude_client and client_id == exclude_client:
                continue
            
            try:
                await websocket.send_text(message_str)
                self._update_client_activity(client_id)
                successful_sends += 1
            except Exception as e:
                logger.error(f"Error broadcasting to client {client_id}: {e}")
                failed_clients.append(client_id)
        
        # Clean up failed connections
        for client_id in failed_clients:
            await self._handle_connection_error(client_id)
        
        if failed_clients:
            logger.warning(f"Failed to send message to {len(failed_clients)} clients")
        
        return successful_sends
    
    async def broadcast_user_count(self) -> None:
        """Broadcast current user count to all clients."""
        user_count_message = WebSocketMessage(
            type=MessageType.USER_COUNT,
            client_id="server",
            payload={"count": self.active_connections_count}
        )
        await self.broadcast(user_count_message)
    
    def add_to_board_state(self, action: Dict[str, Any]) -> None:
        """
        Add an action to the board state.
        
        Args:
            action: The action to add to the board state
        """
        action_type = action.get("type")
        
        if action_type == MessageType.CLEAR:
            self._board_state.clear()
            logger.info("Board state cleared")
        elif action_type in [MessageType.DRAW, MessageType.TEXT]:
            self._board_state.append(action)
            logger.debug(f"Added {action_type} action to board state")
    
    def get_connection_info(self, client_id: str) -> Optional[ConnectionInfo]:
        """
        Get connection information for a specific client.
        
        Args:
            client_id: The client identifier
        
        Returns:
            ConnectionInfo if client exists, None otherwise
        """
        return self._connection_info.get(client_id)
    
    def get_all_connection_info(self) -> List[ConnectionInfo]:
        """Get connection information for all connected clients."""
        return list(self._connection_info.values())
    
    async def cleanup_inactive_connections(self, timeout_seconds: int = 300) -> int:
        """
        Clean up connections that have been inactive for too long.
        
        Args:
            timeout_seconds: Inactivity timeout in seconds
        
        Returns:
            Number of connections cleaned up
        """
        current_time = time.time()
        inactive_clients = []
        
        for client_id, last_activity in self._client_activity.items():
            if current_time - last_activity > timeout_seconds:
                inactive_clients.append(client_id)
        
        for client_id in inactive_clients:
            logger.info(f"Cleaning up inactive client: {client_id}")
            await self.disconnect(client_id)
        
        return len(inactive_clients)
    
    async def _send_board_state(self, websocket: WebSocket) -> None:
        """Send current board state to a specific WebSocket."""
        board_state_message = WebSocketMessage(
            type=MessageType.BOARD_STATE,
            client_id="server",
            payload={"actions": self._board_state}
        )
        await websocket.send_text(board_state_message.json())
    
    def _update_client_activity(self, client_id: str) -> None:
        """Update the last activity timestamp for a client."""
        self._client_activity[client_id] = time.time()
        if client_id in self._connection_info:
            self._connection_info[client_id].last_activity = time.time()
    
    async def _handle_connection_error(self, client_id: str) -> None:
        """Handle connection errors by cleaning up the client."""
        logger.warning(f"Handling connection error for client: {client_id}")
        await self.disconnect(client_id)
