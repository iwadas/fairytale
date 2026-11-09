"""Data access for background music tracks. Never commits; returns ORM objects."""

import uuid
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Music


async def get(session: AsyncSession, music_id: str) -> Music | None:
    result = await session.execute(select(Music).where(Music.id == music_id))
    return result.scalars().first()


def add(session: AsyncSession, *, project_id: str, **fields: Any) -> Music:
    """Add a track with defaults (empty name/src, 30s, layer 4), overridden by ``fields``."""
    music = Music(
        id=str(uuid.uuid4()),
        project_id=project_id,
        name="",
        src="",
        start_time=0.0,
        duration=30.0,
        layer=4,
    )
    for key, value in fields.items():
        setattr(music, key, value)
    session.add(music)
    return music


async def update(session: AsyncSession, music_id: str, **fields: Any) -> Music | None:
    music = await get(session, music_id)
    if music is not None:
        for key, value in fields.items():
            setattr(music, key, value)
    return music


async def delete_by_id(session: AsyncSession, music_id: str) -> None:
    await session.execute(delete(Music).where(Music.id == music_id))
