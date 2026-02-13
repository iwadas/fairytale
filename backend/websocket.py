from fastapi import WebSocket
from typing import List, Dict, Any

class ConnectionManager:
    """
    Singleton class to manage WebSocket connections and broadcasting.
    """
    def __init__(self):
        # This list stores all currently active connections in memory
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accepts a new connection and adds it to the list."""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """Removes a connection from the list."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast_message(self, message: str):
        """
        Public method to broadcast a message to all connected clients.
        Call this from anywhere in your app.
        """
        print(f"Broadcasting message to {len(self.active_connections)} clients: {str(message)}")
        # Iterate over copy to avoid modification errors during iteration
        for connection in self.active_connections[:]: 
            try:
                await connection.send_text(message)
            except Exception:
                # If sending fails (e.g., socket closed unexpectedly), remove it
                self.disconnect(connection)

    async def broadcast_json(self, message: Dict[str, Any]):
        """
        Automatically serializes a Python dict to a JSON string
        and sends it to all clients.
        """
        print(f"Broadcasting JSON message to {len(self.active_connections)} clients: {str(message)}")
        for connection in self.active_connections[:]:
            try:
                # websocket.send_json automatically dumps the dict to a string
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)

# Create a single global instance
socket_manager = ConnectionManager()