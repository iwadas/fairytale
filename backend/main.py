from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from websocket import socket_manager  # Import the global instance

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Your frontend origin
    allow_credentials=False,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

class NoCacheStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return response

app.mount("/static", NoCacheStaticFiles(directory="static"), name="static")


# from routers.characters import router as characters_router
from routers.projects import router as projects_router
from routers.generators import router as generators_router
from routers.scenes import router as scenes_router
from routers.voiceovers import router as voiceovers_router
from routers.music import router as music_router
from routers.settings import router as settings_router
# from routers.images_packages import router as images_packages_router

@app.websocket("/ws")
async def global_ws(websocket: WebSocket):
    await socket_manager.connect(websocket)
    try:
        while True:
            # We must await 'receive' to keep the socket open
            # even if we aren't using the incoming data for logic
            await websocket.receive_text()
    except WebSocketDisconnect:
        socket_manager.disconnect(websocket)


@app.websocket("/ws/responses")
async def responses_ws(websocket: WebSocket):
    await socket_manager.connect(websocket, type="responses")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        socket_manager.disconnect(websocket)

@app.websocket("/ws/scene/generate-video/{scene_id}")
async def scene_generation_ws(websocket: WebSocket, scene_id: str):
    await socket_manager.connect(websocket, type="scene_generation", scene_id=scene_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        socket_manager.disconnect(websocket, scene_id=scene_id)

# app.include_router(characters_router)
app.include_router(projects_router)
app.include_router(generators_router)
app.include_router(scenes_router)
app.include_router(voiceovers_router)
app.include_router(music_router)
app.include_router(settings_router)
# app.include_router(images_packages_router)