"""Background-music use-cases: CRUD, duplication, upload and source change."""

import logging
import os

from fastapi import UploadFile
from pydub import AudioSegment
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Music
from app.media.storage import save_file
from app.repositories import music as music_repo
from app.schemas.music import DuplicateMusicIn, MusicOut
from app.services.errors import NotFoundError

logger = logging.getLogger(__name__)


def get_audio_duration(audio_file_path: str) -> float:
    """Duration in seconds; 0.0 for a missing or undecodable file."""
    if not os.path.exists(audio_file_path):
        return 0.0
    try:
        audio = AudioSegment.from_file(audio_file_path)
        return len(audio) / 1000.0
    except Exception as e:
        logger.exception("Error calculating duration of %s: %s", audio_file_path, e)
        return 0.0


async def _get_or_404(session: AsyncSession, music_id: str) -> Music:
    music = await music_repo.get(session, music_id)
    if music is None:
        raise NotFoundError("Music not found")
    return music


async def create_music(session: AsyncSession, project_id: str, start_time: float) -> Music:
    music = music_repo.add(session, project_id=project_id, start_time=start_time)
    await session.commit()
    return music


async def duplicate_music(session: AsyncSession, music_id: str, overrides: DuplicateMusicIn) -> Music:
    """Copy a track. Falsy overrides fall back to the source values; the default
    start is right after the source track."""
    source = MusicOut.from_model(await _get_or_404(session, music_id))
    music = music_repo.add(
        session,
        project_id=source.project_id,
        src=source.src,
        name=source.name,
        duration=overrides.duration or source.duration,
        start_time=overrides.start_time or source.start_time + source.duration,
        cut_start=overrides.cut_start or source.cut_start,
        cut_end=overrides.cut_end or source.cut_end,
        layer=overrides.layer or source.layer,
    )
    await session.commit()
    return music


async def upload_music(session: AsyncSession, music_id: str, music_file: UploadFile) -> Music:
    """Store an uploaded audio file as the track's source."""
    music = await _get_or_404(session, music_id)

    src = await save_file(music_file, type="music")
    # NOTE: pydub decoding blocks the event loop (audit §3.4); kept as before.
    duration = get_audio_duration(src)

    music.src = src
    music.name = music_file.filename.replace(" ", "_")
    music.duration = duration
    await session.commit()
    return music


async def set_music_source(session: AsyncSession, music_id: str, src: str) -> Music:
    """Point the track at an existing file path (name and duration derived from it)."""
    music = await _get_or_404(session, music_id)

    duration = get_audio_duration(src)

    music.name = src.split("/")[-1].replace(" ", "_")
    music.src = src
    music.duration = duration
    await session.commit()
    return music


async def delete_music(session: AsyncSession, music_id: str) -> None:
    await music_repo.delete_by_id(session, music_id)
    await session.commit()
