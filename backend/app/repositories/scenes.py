"""Data access for scenes and scene images. Never commits; returns ORM objects."""

import uuid
from collections.abc import Iterable, Mapping
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Scene, SceneImage


async def get(session: AsyncSession, scene_id: str, *, with_images: bool = False) -> Scene | None:
    stmt = select(Scene).where(Scene.id == scene_id)
    if with_images:
        stmt = stmt.options(selectinload(Scene.images))
    result = await session.execute(stmt)
    return result.scalars().first()


def add(
    session: AsyncSession,
    *,
    project_id: str,
    id: str | None = None,
    video_src: str | None = None,
    duration: float | None = 0.0,
    video_prompt: str | None = None,
    start_time: float | None = 0.0,
    cut_start: float | None = 0.0,
    cut_end: float | None = 0.0,
    layer: int | None = 2,
    images: Iterable[Mapping[str, Any]] | None = None,
) -> Scene:
    """Add a scene and, optionally, its images.

    Images are added as separate rows (not through ``scene.images``), so the
    returned scene's ``images`` relationship stays unloaded.
    """
    scene_id = id if id is not None else str(uuid.uuid4())
    scene = Scene(
        id=scene_id,
        project_id=project_id,
        video_src=video_src,
        duration=duration,
        start_time=start_time,
        video_prompt=video_prompt,
        cut_start=cut_start,
        cut_end=cut_end,
        layer=layer,
    )
    session.add(scene)
    for image in images or ():
        session.add(
            SceneImage(
                scene_id=scene_id,
                src=image.get("src", ""),
                prompt=image.get("prompt", ""),
                time=image.get("time", "start"),
                idea=image.get("idea", ""),
                style=image.get("style", ""),
            )
        )
    return scene


async def update(session: AsyncSession, scene_id: str, **fields: Any) -> Scene | None:
    scene = await get(session, scene_id)
    if scene is not None:
        for key, value in fields.items():
            setattr(scene, key, value)
    return scene


async def delete_by_id(session: AsyncSession, scene_id: str) -> None:
    # Bulk delete: bypasses the images delete-orphan cascade (audit B8).
    await session.execute(delete(Scene).where(Scene.id == scene_id))


async def delete_image(session: AsyncSession, image_id: str) -> None:
    await session.execute(delete(SceneImage).where(SceneImage.id == image_id))


async def get_image(session: AsyncSession, image_id: str) -> SceneImage | None:
    result = await session.execute(select(SceneImage).where(SceneImage.id == image_id))
    return result.scalars().first()


def add_image(
    session: AsyncSession, *, scene_id: str, src: str, prompt: str | None, time: str | None
) -> SceneImage:
    image = SceneImage(id=str(uuid.uuid4()), scene_id=scene_id, src=src, prompt=prompt, time=time)
    session.add(image)
    return image
