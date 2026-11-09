"""Background-music schemas (requests + both response formats)."""

from typing import Optional

from pydantic import BaseModel

from app.db.models import Music
from app.schemas.common import Number, ORMModel, RequestModel


class MusicOut(BaseModel):
    id: str
    project_id: str | None
    name: str | None
    src: str | None
    start_time: Number | None
    duration: Number | None
    cut_start: Number
    cut_end: Number
    layer: Number

    @classmethod
    def from_model(cls, music: Music) -> "MusicOut":
        return cls(
            id=music.id,
            project_id=music.project_id,
            name=music.name,
            src=music.src,
            start_time=music.start_time,
            duration=music.duration,
            cut_start=music.cut_start or 0.0,
            cut_end=music.cut_end or 0.0,
            layer=music.layer or 4,
        )


class MusicRecord(ORMModel):
    """Raw format (``GET /projects/{id}``)."""

    id: str
    project_id: str | None
    name: str | None
    src: str | None
    start_time: Number | None
    duration: Number | None
    cut_start: Number | None
    cut_end: Number | None
    layer: Number | None


# --- requests -------------------------------------------------------------------


class CreateMusicIn(RequestModel):
    start_time: float


class DuplicateMusicIn(RequestModel):
    """Falsy values (0, None) fall back to the source track; ``layer`` defaults to 2."""

    start_time: Optional[float] = 0.0
    cut_start: Optional[float] = 0.0
    cut_end: Optional[float] = 0.0
    duration: Optional[float] = 0.0
    layer: Optional[int] = 2


class UpdateMusicIn(RequestModel):
    src: str


class UploadMusicOut(BaseModel):
    message: str
    music: MusicOut
