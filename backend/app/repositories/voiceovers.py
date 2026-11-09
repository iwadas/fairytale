"""Data access for voiceovers. Never commits; returns ORM objects.

``timestamps`` and ``text_with_pauses`` are JSON stored in Text columns: values
that are not already strings are JSON-encoded here; ``None`` stays NULL.
"""

import json
import uuid
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Voiceover

JSON_TEXT_FIELDS = ("timestamps", "text_with_pauses")


def _encode(value: Any) -> Any:
    if value is not None and not isinstance(value, str):
        return json.dumps(value)
    return value


async def get(session: AsyncSession, voiceover_id: str) -> Voiceover | None:
    result = await session.execute(select(Voiceover).where(Voiceover.id == voiceover_id))
    return result.scalars().first()


async def list_for_project(session: AsyncSession, project_id: str) -> list[Voiceover]:
    """A project's voiceovers in timeline order."""
    stmt = select(Voiceover).where(Voiceover.project_id == project_id).order_by(Voiceover.start_time.asc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def script_text(session: AsyncSession, project_id: str) -> str:
    """The project's full script: voiceover texts joined in timeline order."""
    return " ".join(vo.text for vo in await list_for_project(session, project_id))


def add(
    session: AsyncSession,
    *,
    project_id: str,
    text: str = "",
    id: str | None = None,
    timestamps: Any = None,
    text_with_pauses: Any = None,
    src: str | None = None,
    start_time: float = 0.0,
    duration: float | None = 4.0,
    cut_start: float | None = 0.0,
    cut_end: float | None = 0.0,
    layer: int | None = 3,
) -> Voiceover:
    if text is None:
        raise ValueError("Text cannot be None")
    if project_id is None:
        raise ValueError("Project ID cannot be None")
    voiceover = Voiceover(
        id=id if id is not None else str(uuid.uuid4()),
        project_id=project_id,
        text=text,
        start_time=start_time,
        timestamps=_encode(timestamps),
        text_with_pauses=_encode(text_with_pauses),
        duration=duration,
        cut_start=cut_start,
        cut_end=cut_end,
        layer=layer,
        src=src,
    )
    session.add(voiceover)
    return voiceover


async def update(session: AsyncSession, voiceover_id: str, **fields: Any) -> Voiceover | None:
    voiceover = await get(session, voiceover_id)
    if voiceover is not None:
        for key, value in fields.items():
            if key in JSON_TEXT_FIELDS and isinstance(value, list):
                value = json.dumps(value)
            setattr(voiceover, key, value)
    return voiceover


async def delete_by_id(session: AsyncSession, voiceover_id: str) -> None:
    await session.execute(delete(Voiceover).where(Voiceover.id == voiceover_id))
