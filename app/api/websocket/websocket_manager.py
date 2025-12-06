"""WebSocket connection management for handling multiple client connections."""
from typing import Dict, Set
from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections for users."""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        """Connect a websocket and accept it."""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        logger.info(f"User {user_id} connected. Total connections: {len(self.active_connections[user_id])}")

    async def disconnect(self, websocket: WebSocket, user_id: str) -> None:
        """Disconnect a websocket from the manager."""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
            logger.info(f"User {user_id} disconnected")

    async def send_personal_message(self, message: dict, user_id: str) -> None:
        """Send a message to all connections of a specific user."""
        
        if user_id not in self.active_connections:
            logger.warning(f"User {user_id} not connected, cannot send message")
            return
            
        disconnected: Set[WebSocket] = set()
        
        for connection in self.active_connections[user_id]:
            try:
                await connection.send_json(data=message)
            except Exception as e:
                logger.error(f"Error sending to user {user_id}: {e}")
                disconnected.add(connection)

        
        for connection in disconnected:
            await self.disconnect(websocket=connection, user_id=user_id)
                
    async def send_message(self, websocket: WebSocket, message: dict) -> None:
        """Send a message to a specific websocket."""
        try:
            await websocket.send_json(data=message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            
    async def broadcast(self, message: dict) -> None:
        """Broadcast a message to all connected users."""
        disconnected_users: Set[str] = set()

        for user_id, connections in self.active_connections.items():
            disconnected_connections: Set[WebSocket] = set()
            
            
            for connection in connections:
                try:
                    await connection.send_json(data=message)
                except Exception as e:
                    logger.error(f"Error broadcasting to {user_id}: {e}")
                    disconnected_connections.add(connection)
            
            
            for conn in disconnected_connections:
                connections.discard(conn)
            
            
            if not connections:
                disconnected_users.add(user_id)

        
        for user_id in disconnected_users:
            del self.active_connections[user_id]

    def get_connection_count(self, user_id: str) -> int:
        """Get number of active connections for a user."""
        return len(self.active_connections.get(user_id, set()))
    
    def get_total_connections(self) -> int:
        """Get total number of active connections across all users."""
        return sum(len(conns) for conns in self.active_connections.values())
    
    def is_connected(self, user_id: str) -> bool:
        """Check if a user has any active connections."""
        return user_id in self.active_connections and len(self.active_connections[user_id]) > 0


manager = WebSocketManager()