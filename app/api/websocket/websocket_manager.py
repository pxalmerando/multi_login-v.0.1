from typing import Dict, Set, Optional
from fastapi import WebSocket

class WebSocketManager:

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: Optional[str]) -> None:
        """
        Connect a websocket to the manager.

        If the user_id is not already in the manager, add it with an empty set of websockets.
        Add the websocket to the set of websockets for the user_id.
        Accept the websocket connection.
        """

        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)

    async def disconnect(self, websocket: WebSocket, user_id: str) -> None:
        """
        Disconnect a websocket from the manager.

        If the user_id has no other active connections, remove the user_id from the manager.
        """

        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)

            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_personal_message(self, message: dict, user_id: int):
        """
        Send a personal message to a user.

        If the user_id has active connections, iterate over the connections and attempt to send the message.
        If any exceptions occur while sending the message, add the connection to the disconnected set.
        After sending the message, iterate over the disconnected set and disconnect each connection.

        Parameters
        ----------
        message : dict
            The message to send to the user.
        user_id : int
            The user_id to send the message to.
        """
        if self.active_connections[user_id]:
            disconnected = set()

            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(data=message)
                except Exception as e:
                    print(f"Error sending personal message to user {user_id}: {e}")
                    disconnected.add(connection)

            for connection in disconnected:
                await self.disconnect(websocket=connection, user_id=user_id)
                
    async def send_message(self, websocket: WebSocket, message: dict):
        """
        Send a message to a user.

        Parameters
        ----------
        websocket : WebSocket
            The websocket to send the message to.
        message : dict
            The message to send to the user.

        Raises
        ------
        Exception
            If an error occurs while sending the message to the user.
        """
        try:
            await websocket.send_json(data=message)
        except Exception as e:
            print(f"Error sending message to user: {e}")
            
    async def broadcast(self, message: dict):

        """
        Broadcast a message to all active connections.

        Iterate over all active connections and attempt to send the message.
        If any exceptions occur while sending the message, add the user_id to the disconnected set.
        After sending the message, iterate over the disconnected set and disconnect each user_id.

        Parameters
        ----------
        message : dict
            The message to broadcast to all active connections.

        """

        disconnected = set()

        for user_id, connections in self.active_connections.items():
            try:
                await connections.send_json(data=message)
            except Exception as e:
                print(f"Error broadcasting message to user {user_id}: {e}")
                disconnected.add(user_id)

        for user_id in disconnected:
            await self.disconnect(user_id=user_id)

    

manager = WebSocketManager()