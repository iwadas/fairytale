import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.realtime.connection_manager import socket_manager  # Import the global instance

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws")
async def global_ws(websocket: WebSocket):
    logger.info("New WebSocket connection established.")
    await socket_manager.connect(websocket)
    try:
        while True:
            # We must await 'receive' to keep the socket open
            # even if we aren't using the incoming data for logic
            await websocket.receive_text()
    except WebSocketDisconnect:
        socket_manager.disconnect(websocket)


@router.websocket("/ws/responses")
async def responses_ws(websocket: WebSocket):
    logger.info("New responses WebSocket connection established.")
    await socket_manager.connect(websocket, connection_type="responses")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        socket_manager.disconnect(websocket)
