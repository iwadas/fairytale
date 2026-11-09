"""Scene use-cases: CRUD, duplication, uploads, LLM prompt helpers and the
background video-generation job."""

import asyncio
import logging
from typing import Any, Optional

from fastapi import UploadFile
from moviepy import VideoFileClip
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm import LLM
from app.ai.video_generation import Diffusion
from app.db.models import Scene, SceneImage
from app.db.session import async_session_maker
from app.media.storage import save_file
from app.realtime.connection_manager import WebSocketTaskManager
from app.repositories import scenes as scene_repo
from app.repositories import voiceovers as voiceover_repo
from app.schemas.scene import DuplicateSceneIn, SceneImageOut
from app.services.errors import NotFoundError
from app.services.prompts import scene_editing_prompts

logger = logging.getLogger(__name__)

NEW_SCENE_DURATION = 3.0


# --- CRUD ---------------------------------------------------------------------------


async def create_scene(session: AsyncSession, project_id: str, start_time: Optional[float]) -> Scene:
    scene = scene_repo.add(session, project_id=project_id, duration=NEW_SCENE_DURATION, start_time=start_time)
    await session.commit()
    return scene


async def duplicate_scene(session: AsyncSession, scene_id: str, overrides: DuplicateSceneIn) -> Scene:
    """Copy a scene (and its images). Falsy overrides fall back to the source values;
    the default start is right after the source scene."""
    source = await scene_repo.get(session, scene_id, with_images=True)
    if source is None:
        raise NotFoundError("Scene not found")

    # Normalise through the serialized form (cut_*/layer defaults applied).
    cut_start = source.cut_start or 0.0
    cut_end = source.cut_end or 0.0
    layer = source.layer or 2
    scene = scene_repo.add(
        session,
        project_id=source.project_id,
        video_src=source.video_src,
        duration=overrides.duration or source.duration,
        start_time=overrides.start_time or source.start_time + source.duration,
        video_prompt=source.video_prompt,
        cut_start=overrides.cut_start or cut_start,
        cut_end=overrides.cut_end or cut_end,
        layer=overrides.layer or layer,
        images=[SceneImageOut.from_model(image).model_dump() for image in source.images],
    )
    await session.commit()
    return scene


async def delete_scene(session: AsyncSession, scene_id: str) -> None:
    await scene_repo.delete_by_id(session, scene_id)
    await session.commit()


async def remove_scene_image(session: AsyncSession, scene_image_id: str) -> None:
    await scene_repo.delete_image(session, scene_image_id)
    await session.commit()


# --- uploads ------------------------------------------------------------------------


def get_video_duration_sync(file_path: str) -> float:
    """Returns video duration in seconds using moviepy (0.0 if unreadable)."""
    try:
        with VideoFileClip(file_path) as clip:
            return clip.duration
    except Exception as e:
        logger.exception("Error getting duration of %s: %s", file_path, e)
        return 0.0


async def upload_scene_video(session: AsyncSession, scene_id: str, video: UploadFile) -> tuple[str, float]:
    """Store the uploaded video for a scene; returns ``(video_src, duration)``."""
    scene = await scene_repo.get(session, scene_id)
    if scene is None:
        raise NotFoundError("Scene not found")

    video_src = await save_file(video, type="scene_video")
    duration = await asyncio.to_thread(get_video_duration_sync, video_src)

    scene.video_src = video_src
    scene.duration = duration
    await session.commit()
    return video_src, duration


async def upload_scene_image(
    session: AsyncSession,
    scene_id: str,
    image: UploadFile,
    time: str,
    scene_image_id: Optional[str],
    scene_image_prompt: Optional[str],
) -> SceneImage:
    """Store an uploaded image as a new scene image, or replace an existing one's file."""
    if await scene_repo.get(session, scene_id) is None:
        raise NotFoundError("Scene not found")

    src = await save_file(image, type="scene_image", remove_watermark_if_present=True)

    if scene_image_id is not None:
        scene_image = await scene_repo.get_image(session, scene_image_id)
        # NOTE (audit B9): an unknown scene_image_id fails here with AttributeError (500).
        if src:
            scene_image.src = src
        if scene_image_prompt is not None:
            scene_image.prompt = scene_image_prompt
        scene_image.time = time
    else:
        scene_image = scene_repo.add_image(
            session, scene_id=scene_id, src=src, prompt=scene_image_prompt, time=time
        )
    await session.commit()
    return scene_image


# --- LLM prompt helpers ---------------------------------------------------------------


async def generate_image_prompts(
    session: AsyncSession, project_id: str, selected_voiceover_text_part: str, additional_info: Optional[str]
) -> list[scene_editing_prompts.Scene]:
    script = await voiceover_repo.script_text(session, project_id)
    messages = scene_editing_prompts.image_prompts_messages(script, selected_voiceover_text_part, additional_info)

    llm = await LLM.create()
    response = await llm.generate(messages=messages, response_format=scene_editing_prompts.ResponseScenes)
    logger.debug("Generated scene image prompts: %s", response.scenes)
    return response.scenes


async def fix_image_prompt(scene_prompt: str, style: Optional[str], style_power: Optional[float]) -> str:
    # NOTE (audit B7): the requested ``style`` is ignored in favour of a hardcoded one.
    messages = scene_editing_prompts.fix_image_prompt_messages(
        scene_prompt, scene_editing_prompts.FIX_IMAGE_PROMPT_STYLE, style_power
    )
    llm = await LLM.create()
    response = await llm.generate(messages=messages, response_format=scene_editing_prompts.FixedPromptResponse)
    return response.prompt


async def fix_video_prompt(
    session: AsyncSession, scene_id: str, new_camera_movement: str, additional_info: Optional[str]
) -> Scene:
    """Rewrite the scene's video prompt for a new camera movement and save it."""
    scene = await scene_repo.get(session, scene_id, with_images=True)
    if scene is None or not scene.images:
        raise NotFoundError("Scene or images not found")

    first_image = SceneImageOut.from_model(scene.images[0])
    messages = scene_editing_prompts.fix_video_prompt_messages(
        current_idea=first_image.idea,
        current_image_prompt=first_image.prompt,
        current_video_prompt=scene.video_prompt,
        new_camera_movement=new_camera_movement,
        additional_info=additional_info,
    )
    llm = await LLM.create()
    response = await llm.generate(messages=messages, response_format=scene_editing_prompts.VideoPromptUpdate)

    scene.video_prompt = response.new_video_prompt
    await session.commit()
    return scene


# --- background video generation ------------------------------------------------------


async def prepare_video_generation(session: AsyncSession, scene_id: str) -> list[dict[str, Any]]:
    """Validate the scene and return the frames (images with a src) to animate."""
    logger.info("Video generation requested for scene %s", scene_id)
    scene = await scene_repo.get(session, scene_id, with_images=True)
    if scene is None:
        raise NotFoundError("Scene not found")

    logger.debug("Scene %s images: %s", scene_id, scene.images)
    return [{"src": image.src, "time": image.time} for image in scene.images if image.src is not None]


async def process_video_task(scene_id: str, prompt: str, duration: float, frames: list):
    """Background job: generate the video with the diffusion provider and save it.

    Runs after the response is sent, so it uses a session of its own. Progress
    and the result are pushed over the WebSocket channels; failures are reported
    there and logged, never raised.
    """
    socket_notification_manager = WebSocketTaskManager(message_type="scene_video_generation", connection_type="global")
    socket_response_manager = WebSocketTaskManager(task_id=f"scene_video_generation_{scene_id}", message_type="scene_video_generation", connection_type="responses")
    try:
        await socket_notification_manager.send_notification(status="init", message="🌐 Connecting to video generation provider...")
        await socket_response_manager.prepare_for_response()
        diffusion_client = await Diffusion.create()

        await socket_notification_manager.send_notification(status="in_progress", message="🎞️ Generating video...")

        video_src = await diffusion_client.generate(
            prompt=prompt,
            frames=frames,
            duration=int(duration),
            filename=f"scene_{scene_id}"
        )

        await socket_notification_manager.send_notification(status="in_progress", message="📁 Saving video...")
        async with async_session_maker() as session:
            await scene_repo.update(session, scene_id, video_src=video_src, duration=duration)
            await session.commit()
        await socket_notification_manager.send_notification(status="finished", message="✅ Video saved successfully!")

        await socket_response_manager.send_response(status="completed", data={"video_src": video_src}, source={"scene_id": scene_id})

    except Exception as e:
        await socket_notification_manager.send_notification(status="failed", message=f"❌ Video generation failed. Error: {e}")
        await socket_response_manager.send_response_failed()
        logger.exception("Background video generation failed for scene %s: %s", scene_id, e)
