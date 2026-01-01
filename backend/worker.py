import asyncio  # ← make sure this is imported
from huey import SqliteHuey
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession
from sqlalchemy import select

from db import Scene, SceneImage # ← your models + Base
from services import generate_video, filename_from_name  # your video generator

# ── Global engine & session factory ──
# IMPORTANT: use the same DATABASE_URL as in your main FastAPI app!
DATABASE_URL = "sqlite+aiosqlite:///./film.db"  # ← adjust to your real URL
# For postgres → "postgresql+asyncpg://user:pass@localhost/dbname"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,                     # set True only for debugging
    future=True,
    # connect_args={"check_same_thread": False}  # only needed for plain sqlite (not aiosqlite)
)

# Factory for creating new AsyncSession instances
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,         # Very useful: prevents unwanted expires after commit
    autoflush=True,
)

# Huey instance (SQLite backend)
huey = SqliteHuey(
    name="my_fastapi_app",
    filename="queue.db",
    results=True,
    store_none=False,
)

# ── Helper to get fresh session in tasks ──
async def get_task_session() -> AsyncSession:
    async with async_session_maker() as session:
        yield session

@huey.task()  # add retries=2, retry_delay=30 if you want auto-retry
def generate_scene_video_task(
    scene_id: str,
    prompt: str,
    duration: float = 5.0,
):
    """
    Huey task – must be synchronous.
    We run the async logic in a fresh event loop.
    """
    print(f"Starting task for scene {scene_id}")  # ← you should see this in worker logs

    # This is the cleanest way in Python 3.7+
    result = asyncio.run(run_task_async(scene_id, prompt, duration))

    print(f"Task finished for scene {scene_id}")
    return result


async def run_task_async(scene_id: str, prompt: str, duration: float):
    """All the async code lives here"""
    async with async_session_maker() as session:
        async with session.begin():
            scene = await session.get(Scene, scene_id)
            if not scene:
                raise ValueError(f"Scene {scene_id} not found")

            result = await session.execute(
                select(SceneImage)
                .filter_by(scene_id=scene_id)
                .order_by(SceneImage.time)
            )
            scene_images_list = result.scalars().all()

            frames = [
                {"src": img.src, "time": img.time}
                for img in scene_images_list
                if img.src and img.time != 'mid'
            ]

            filename = filename_from_name(f"scene_{scene_id}")

            video_path = generate_video(
                directory="static/videos/scenes",
                filename=filename,
                prompt=prompt,
                negative_prompt="",
                frames=frames,
                duration=int(duration)
            )

            scene.video_src = video_path
            scene.video_prompt = prompt
            scene.duration = duration

    print(f"Video generated for scene {scene_id} → {video_path}")
    return {"status": "success", "scene_id": scene_id, "video_url": video_path}