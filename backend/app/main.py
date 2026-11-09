from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

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


# from app.api.routers.characters import router as characters_router
from app.api.routers.ws import router as ws_router
from app.api.routers.projects import router as projects_router
from app.api.routers.generators import router as generators_router
from app.api.routers.scenes import router as scenes_router
from app.api.routers.voiceovers import router as voiceovers_router
from app.api.routers.music import router as music_router
from app.api.routers.settings import router as settings_router

app.include_router(ws_router)
# app.include_router(characters_router)
app.include_router(projects_router)
app.include_router(generators_router)
app.include_router(scenes_router)
app.include_router(voiceovers_router)
app.include_router(music_router)
app.include_router(settings_router)
