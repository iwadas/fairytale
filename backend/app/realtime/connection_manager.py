import logging
from fastapi import WebSocket
from typing import List, Dict, Any, Optional
import uuid

logger = logging.getLogger(__name__)

class ConnectionManager:
    """
    Singleton class to manage WebSocket connections and broadcasting.
    """
    def __init__(self):
        # Use a dictionary to map connection types. This scales infinitely!
        self.active_connections: Dict[str, List[WebSocket]] = {
            "global": [],
            "responses": []
        }

    async def connect(self, websocket: WebSocket, connection_type: str = "global"):
        """Accepts a new connection and routes it to the correct pool."""
        await websocket.accept()
        logger.info("New WebSocket connection established for '%s'", connection_type)

        if connection_type in self.active_connections:
            self.active_connections[connection_type].append(websocket)
        else:
            # Fallback/Error handling if an unknown type is passed
            logger.warning("Attempted to connect with unknown type '%s'", connection_type)

    def disconnect(self, websocket: WebSocket):
        """Removes a connection from whichever list it belongs to."""
        for conn_list in self.active_connections.values():
            if websocket in conn_list:
                conn_list.remove(websocket)
                return # Exit early once found and removed

    async def broadcast_json(self, message: Dict[str, Any], connection_type: str = "global"):
        """
        Sends JSON to all clients in the specified connection pool.
        """
        if connection_type not in self.active_connections:
            return

        connections = self.active_connections[connection_type]
        logger.debug("Broadcasting JSON to %d '%s' clients.", len(connections), connection_type)
        
        # Iterate over a copy of the list [:] to allow safe removal during iteration
        for connection in connections[:]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning("Error sending message, disconnecting socket: %s", e)
                self.disconnect(connection)



class WebSocketTaskManager:
    """
    Helper class to easily send status updates for a specific task.
    """
    def __init__(self, message_type: str, task_id: Optional[str] = None, connection_type: str = "global"):
        # We pass task_id IN, so it matches what the REST API gave the frontend
        if(not task_id):
            task_id = str(uuid.uuid4())
        self.task_id = task_id 
        self.message_type = message_type
        self.connection_type = connection_type

    async def send_notification(self, status: str, message: Any):
        """
        Helper method to send a standardized JSON payload.
        """
        payload = {
            "type": self.message_type, 
            "status": status,  
            "task_id": self.task_id,    
            "data": message             
        }
        await socket_manager.broadcast_json(message=payload, connection_type=self.connection_type)


    async def prepare_for_response(self):
        """
        Optional helper to send an initial 'pending' status before starting a long task.
        """
        await self.send_response(status="pending", data=None)

    async def send_response_failed(self):
        """
        Helper to send a standardized failure response.
        """
        await self.send_response(status="failed", data=None)


    async def send_response(self, status: str = "completed", data: Optional[Any] = None, source = None):
        """
        Helper method to send a response payload. Can include an optional 'source' field.
        """
        payload = {
            "type": self.message_type, 
            "status": status,  
            "task_id": self.task_id,    
            "data": data             
        }

        if source:
            payload["source"] = source
        await socket_manager.broadcast_json(message=payload, connection_type=self.connection_type)




# Create the single global instance
socket_manager = ConnectionManager()