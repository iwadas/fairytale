"""Project use-cases: listing, script generation, the create-from-script pipeline,
timeline updates, rendering and copying."""

import logging
import os
import re
from collections.abc import Iterator
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm import LLM
from app.core.config import get_settings
from app.db.models import Project
from app.pipeline.render.builder import VideoBuilder
from app.pipeline.script.scene_generator import generate_scenes, split_script
from app.pipeline.script.script_generator import ScriptGenerator
from app.realtime.connection_manager import WebSocketTaskManager
from app.repositories import music as music_repo
from app.repositories import projects as project_repo
from app.repositories import scenes as scene_repo
from app.repositories import voiceovers as voiceover_repo
from app.schemas.project import ProjectOut, ScriptIn

logger = logging.getLogger(__name__)

WORDS_PER_MINUTE = 180
STORY_SAMPLES_COUNT = 1
GENERATED_SCENE_DURATION = 3.0


# --- queries ------------------------------------------------------------------------


async def list_projects(session: AsyncSession) -> list[tuple[Project, str | None]]:
    return await project_repo.list_with_thumbnails(session)


async def get_project(session: AsyncSession, project_id: str) -> Project | None:
    return await project_repo.get_with_graph(session, project_id)


# --- script generation ----------------------------------------------------------------


async def generate_scripts(request: ScriptIn) -> list[str]:
    """Generate ``STORY_SAMPLES_COUNT`` script candidates with the LLM (no DB writes)."""
    # Estimated word count at 180 words per minute.
    word_count = request.duration * WORDS_PER_MINUTE / 60

    story_data = None
    if request.data:
        story_data = request.data
    elif request.gather_data:
        pass  # TODO: gather story data (legacy gather_story_data was never ported)

    llm_client = await LLM.create()

    scripts = []

    task = WebSocketTaskManager(connection_type="global", message_type="script_generation")

    await task.send_notification(
        message=f"🎬 Initializing script generation for {STORY_SAMPLES_COUNT} story samples...",
        status="init",
    )

    for i in range(STORY_SAMPLES_COUNT):

        await task.send_notification(
            message=f"🖊️ Generating story sample {i+1} of {STORY_SAMPLES_COUNT}...",
            status="in_progress",
        )
        script_generator = ScriptGenerator(
            llm_client=llm_client,
            topic=request.topic,
            description=request.description,
            story_data=story_data,
            reference_stories=request.reference_stories,
            persistant_characters=request.persistant_characters,
            word_limit=word_count
        )

        scripts.append(await script_generator.generate())

    await task.send_notification(
        message=f"🎉 Finished generating story sample {STORY_SAMPLES_COUNT} of {STORY_SAMPLES_COUNT}.",
        status="finished"
    )

    return scripts


# --- create project from a script -------------------------------------------------------


def layout_scenes(start_time: float, scenes: list[dict[str, Any]]) -> Iterator[tuple[float, int, dict[str, Any]]]:
    """Place a script part's scenes on the timeline as ``(start_time, layer, scene)``.

    There are more scenes than narration time, so they are spread over two layers:
    the layer alternates 2, 1, 2, 1, ... and the time advances by
    ``GENERATED_SCENE_DURATION`` after every layer-1 scene.
    """
    layer = 2
    for scene in scenes:
        yield start_time, layer, scene
        if layer == 1:
            start_time += GENERATED_SCENE_DURATION
        layer = 2 if layer == 1 else 1


async def create_project(session: AsyncSession, topic: str, script: str) -> str:
    """Split the script, generate scenes with the LLM, then persist the project with
    its voiceovers and scenes in one transaction. Returns the new project id."""
    task = WebSocketTaskManager(connection_type="global", message_type="create_project")

    await task.send_notification(
        message=f"🎬 Initializing project creation for topic: {topic}...",
        status="init"
    )

    await task.send_notification(
        message=f"✂️ Splitting script...",
        status="in_progress"
    )

    splitted_script = split_script(script)

    await task.send_notification(
        message=f"🖼️ Adding scenes..",
        status="in_progress"
    )

    llm_client = await LLM.create()

    script_with_scenes = await generate_scenes(
        llm_client=llm_client,
        script=script,
        splitted_script=splitted_script,
    )

    await task.send_notification(
        message=f"💾 Creating project in database...",
        status="in_progress"
    )

    project = project_repo.add(session, name=topic, type="BASIC")

    await task.send_notification(
        message=f"🔊 Saving voiceovers and scenes...",
        status="in_progress"
    )

    for script_part in script_with_scenes:
        start_time = float(script_part.get("start_time", 0.0))

        voiceover_repo.add(
            session,
            project_id=project.id,
            text=script_part["text"],
            start_time=start_time,
            duration=script_part.get("duration", 0.0),
        )

        for scene_start, layer, scene in layout_scenes(start_time, script_part["scenes"]):
            scene_repo.add(
                session,
                project_id=project.id,
                start_time=scene_start,
                video_prompt=scene["video_prompt"],
                duration=GENERATED_SCENE_DURATION,
                layer=layer,
                images=[
                    {
                        "prompt": scene["image_prompt"],
                        "time": "start",
                        "idea": scene["idea"],
                        "style": scene["style"],
                    }
                ],
            )

    await session.commit()

    await task.send_notification(
        message=f"🎉 Project created successfully!",
        status="finished"
    )

    return project.id


# --- edit -------------------------------------------------------------------------------


async def delete_project(session: AsyncSession, project_id: str) -> None:
    await project_repo.delete_by_id(session, project_id)
    await session.commit()


TIMELINE_UPDATERS = {
    "scene": scene_repo.update,
    "voiceover": voiceover_repo.update,
    "music": music_repo.update,
}


def _timeline_changes(element: dict[str, Any]) -> dict[str, Any]:
    """Column values for one timeline element.

    NOTE (audit B11): missing keys fall back to start 0.0, duration 4.0, layer 0
    and cut_* None, overwriting the stored values.
    """
    changes = {
        "start_time": element.get("start_time", 0.0),
        "duration": element.get("duration", 4.0),
        "layer": element.get("layer", 0),
        "cut_start": element.get("cut_start"),
        "cut_end": element.get("cut_end"),
    }
    for key in ("video_prompt", "text", "text_with_pauses"):
        if element.get(key) is not None:
            changes[key] = element[key]
    return changes


async def update_timeline(session: AsyncSession, timeline_elements: list) -> None:
    """Apply the editor's timeline (scenes, voiceovers, music) in one transaction.

    Unknown ids and unknown element types are ignored.
    """
    for element in timeline_elements:
        element_id = element["id"]
        changes = _timeline_changes(element)
        updater = TIMELINE_UPDATERS.get(element["type"])
        if updater is not None:
            await updater(session, element_id, **changes)
    await session.commit()


# --- render -----------------------------------------------------------------------------


def get_save_name(name: str) -> str:
    """A filesystem-safe file name: Windows-reserved characters removed, spaces -> ``_``."""
    name = re.sub(r'[\\/:*?"<>|]', '', name)
    return name.replace(" ", "_")


async def render_project(session: AsyncSession, project_id: str) -> str:
    """Render the project to ``<render_output_dir>/<name>.mp4``; returns the path.

    NOTE: ``VideoBuilder.build()`` is synchronous and blocks the event loop (audit §3.4).
    A missing project fails with an unhandled error (500), as before.
    """
    project = await project_repo.get_with_graph(session, project_id)
    project_data = ProjectOut.from_model(project).model_dump()

    output_dir = get_settings().render_output_dir
    os.makedirs(output_dir, exist_ok=True)
    output_filename = f"{get_save_name(project_data['name'])}.mp4"
    output_path = os.path.join(output_dir, output_filename)
    logger.info("Starting video build for project %s -> %s", project_id, output_path)

    video_builder = VideoBuilder(project=project_data, output_filename=output_path) \
        .set_resolution(640, 640) \
        .set_subtitle_style("karaoke_remotion") \
        .add_font("static/default/fonts/Unna-Regular.ttf") \
        .add_subtitle_shadow() \
        .set_subtitle_color("white") \
        .set_subtitle_special_color("rgb(230, 163, 49)")

    video_builder.build()
    return output_path


# --- copy -------------------------------------------------------------------------------


async def copy_project(session: AsyncSession, project_id: str, suffix: str = " (Copy)") -> Project:
    """Deep-copy a project (scenes + images, voiceovers, music) in one transaction.

    Elements are copied through their serialized form, so ``cut_*``/``layer``
    defaults are materialised in the copy. Characters and places are not copied.
    A missing project fails with an unhandled error (500), as before.
    """
    source = ProjectOut.from_model(await project_repo.get_with_graph(session, project_id))

    copy = project_repo.add(session, name=f"{source.name}{suffix}", type=source.type)

    for scene in source.scenes:
        scene_repo.add(
            session,
            project_id=copy.id,
            video_src=scene.video_src,
            duration=scene.duration,
            video_prompt=scene.video_prompt,
            start_time=scene.start_time,
            cut_start=scene.cut_start,
            cut_end=scene.cut_end,
            layer=scene.layer,
            images=[image.model_dump() for image in scene.images],
        )

    for vo in source.voiceovers:
        voiceover_repo.add(
            session,
            project_id=copy.id,
            text=vo.text,
            timestamps=vo.timestamps,
            text_with_pauses=vo.text_with_pauses,
            src=vo.src,
            start_time=vo.start_time,
            duration=vo.duration,
            cut_start=vo.cut_start,
            cut_end=vo.cut_end,
            layer=vo.layer,
        )

    for music in source.background_music:
        music_repo.add(
            session,
            project_id=copy.id,
            name=music.name,
            src=music.src,
            start_time=music.start_time,
            duration=music.duration,
            cut_start=music.cut_start,
            cut_end=music.cut_end,
            layer=music.layer,
        )

    await session.commit()
    return copy
