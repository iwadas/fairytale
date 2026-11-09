from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.realtime.connection_manager import socket_manager  # Import the global instance

router = APIRouter()


@router.websocket("/ws")
async def global_ws(websocket: WebSocket):
    print("New WebSocket connection established.")
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
    print("New Responses WebSocket connection established.")
    await socket_manager.connect(websocket, connection_type="responses")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        socket_manager.disconnect(websocket)
