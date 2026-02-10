from worker import huey, async_session_maker
import asyncio

from sqlalchemy import select
from db import Scene, SceneImage # ← your models + Base
from services import generate_video, filename_from_name  # your video generator

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
    result = asyncio.run(run_generate_video_task_async(scene_id, prompt, duration))

    print(f"Task finished for scene {scene_id}")
    return result


async def run_generate_video_task_async(scene_id: str, prompt: str, duration: float):
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
