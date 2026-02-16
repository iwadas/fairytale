from fastapi import WebSocket
from typing import List, Dict, Any

class ConnectionManager:
    """
    Singleton class to manage WebSocket connections and broadcasting.
    """
    def __init__(self):
        # This list stores all currently active connections in memory
        self.global_connections: List[WebSocket] = []
        self.scene_generation_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, type: str = "global", **kwargs):
        """Accepts a new connection and adds it to the list."""
        await websocket.accept()
        if type == "global":
            self.global_connections.append(websocket)
        elif type == "scene_generation":
            scene_id = kwargs.get("scene_id")
            if scene_id not in self.scene_generation_connections:
                self.scene_generation_connections[scene_id] = []
            self.scene_generation_connections[scene_id].append(websocket)

    def disconnect(self, websocket: WebSocket):
        """Removes a connection from the list."""
        if websocket in self.global_connections:
            self.global_connections.remove(websocket)
        # Remove from scene generation connections if it exists
        for _, connections in self.scene_generation_connections.items():
            if websocket in connections:
                connections.remove(websocket)
                break

    async def broadcast_message(self, message: str, type: str = "global", **kwargs):
        """
        Public method to broadcast a message to all connected clients.
        Call this from anywhere in your app.
        """
        if type == "global":
            print(f"Broadcasting message to {len(self.global_connections)} global clients: {str(message)}")
            for connection in self.global_connections[:]:
                try:
                    await connection.send_text(message)
                except Exception:
                    self.disconnect(connection)
        elif type == "scene_generation":
            scene_id = kwargs.get("scene_id")
            if scene_id in self.scene_generation_connections:
                connections = self.scene_generation_connections[scene_id]
                print(f"Broadcasting message to {len(connections)} scene generation clients for scene {scene_id}: {str(message)}")
                for connection in connections[:]:
                    try:
                        await connection.send_text(message)
                    except Exception:
                        self.disconnect(connection)

    async def broadcast_json(self, type: str = "global", message: Dict[str, Any] = None, **kwargs):
        """
        Automatically serializes a Python dict to a JSON string
        and sends it to all clients.
        """
        if type == "global":
            print(f"Broadcasting JSON message to {len(self.global_connections)} global clients: {str(message)}")
            for connection in self.global_connections[:]:
                try:
                    await connection.send_json(message)
                except Exception:
                    self.disconnect(connection)
        elif type == "scene_generation":
            scene_id = kwargs.get("scene_id")
            if scene_id in self.scene_generation_connections:
                connections = self.scene_generation_connections[scene_id]
                print(f"Broadcasting JSON message to {len(connections)} scene generation clients for scene {scene_id}: {str(message)}")
                for connection in connections[:]:
                    try:
                        await connection.send_json(message)
                    except Exception:
                        self.disconnect(connection)

        for connection in self.active_connections[:]:
            try:
                # websocket.send_json automatically dumps the dict to a string
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)

# Create a single global instance
socket_manager = ConnectionManager()