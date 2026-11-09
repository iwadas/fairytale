"""Voiceover use-cases: CRUD, duplication, combining and TTS generation."""

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.tts import TTS
from app.db.models import Voiceover
from app.realtime.connection_manager import WebSocketTaskManager
from app.repositories import voiceovers as voiceover_repo
from app.schemas.voiceover import DuplicateVoiceoverIn, VoiceoverOut
from app.services.errors import NotFoundError

logger = logging.getLogger(__name__)


async def create_voiceover(session: AsyncSession, project_id: str, start_time: float) -> Voiceover:
    voiceover = voiceover_repo.add(session, project_id=project_id, text="", start_time=start_time)
    await session.commit()
    return voiceover


async def duplicate_voiceover(session: AsyncSession, voiceover_id: str, overrides: DuplicateVoiceoverIn) -> Voiceover:
    """Copy a voiceover. Falsy overrides fall back to the source values; the default
    start is right after the source voiceover."""
    source = await voiceover_repo.get(session, voiceover_id)
    if source is None:
        raise NotFoundError("Voiceover not found")

    # Copy through the serialized form (decoded JSON, cut_*/layer defaults applied).
    data = VoiceoverOut.from_model(source)
    voiceover = voiceover_repo.add(
        session,
        project_id=data.project_id,
        src=data.src,
        text=data.text,
        text_with_pauses=data.text_with_pauses,
        timestamps=data.timestamps,
        duration=overrides.duration or data.duration,
        start_time=overrides.start_time or data.start_time + data.duration,
        cut_start=overrides.cut_start or data.cut_start,
        cut_end=overrides.cut_end or data.cut_end,
        layer=overrides.layer or data.layer,
    )
    await session.commit()
    return voiceover


async def combine_voiceovers(session: AsyncSession, project_id: str) -> Voiceover:
    """Replace all of a project's voiceovers with one holding their texts in
    timeline order. Atomic: the deletes and the insert commit together."""
    voiceovers = await voiceover_repo.list_for_project(session, project_id)
    combined_text = " ".join(vo.text or "" for vo in voiceovers)

    for vo in voiceovers:
        await voiceover_repo.delete_by_id(session, vo.id)
    combined = voiceover_repo.add(session, project_id=project_id, text=combined_text)

    await session.commit()
    return combined


async def delete_voiceover(session: AsyncSession, voiceover_id: str) -> None:
    await voiceover_repo.delete_by_id(session, voiceover_id)
    await session.commit()


async def generate_voiceover(session: AsyncSession, voiceover_id: str, text: str) -> dict[str, Any]:
    """Synthesize ``text`` with the configured TTS provider and store the result on
    the voiceover; returns the TTS result (src, duration, text, timestamps, ...).

    Raises ``ValueError`` for a missing voiceover or one without stored text
    (unhandled -> 500, audit B10).
    """
    voiceover = await voiceover_repo.get(session, voiceover_id)
    if voiceover is None:
        raise ValueError("Voiceover not found")
    if not voiceover.text:
        raise ValueError("Voiceover text is empty")

    tts_client = await TTS.create()

    task = WebSocketTaskManager(connection_type="global", message_type="voiceover_generation")

    await task.send_notification(
        message=f"🎙️ Initializing voiceover generation...",
        status="init"
    )

    logger.debug("Generating voiceover with text: %s", text)

    tts_result = await tts_client.generate(
        progress_callback=task.send_notification,
        text=text,
    )

    logger.debug("TTS result: %s", tts_result)

    await task.send_notification(
        message=f"📁 Saving generated voiceover...",
        status="in_progress"
    )

    await voiceover_repo.update(session, voiceover_id, **tts_result)
    await session.commit()

    await task.send_notification(
        message=f"✅ Voiceover generation and saving completed.",
        status="finished"
    )

    return tts_result
