"""Voiceover schemas (requests + both response formats)."""

import json
from typing import Any, Optional

from pydantic import BaseModel

from app.db.models import Voiceover
from app.schemas.common import Number, ORMModel, RequestModel


class VoiceoverOut(BaseModel):
    """Serialized format: ``timestamps`` / ``text_with_pauses`` decoded from JSON."""

    id: str
    project_id: str | None
    src: str | None
    text: str | None
    text_with_pauses: Any
    timestamps: Any
    start_time: Number | None
    duration: Number | None
    cut_start: Number
    cut_end: Number
    layer: Number

    @classmethod
    def from_model(cls, voiceover: Voiceover) -> "VoiceoverOut":
        try:
            text_with_pauses = json.loads(voiceover.text_with_pauses) if voiceover.text_with_pauses else []
        except json.JSONDecodeError:
            text_with_pauses = []
        return cls(
            id=voiceover.id,
            project_id=voiceover.project_id,
            src=voiceover.src,
            text=voiceover.text,
            text_with_pauses=text_with_pauses,
            timestamps=json.loads(voiceover.timestamps) if voiceover.timestamps else [],
            start_time=voiceover.start_time,
            duration=voiceover.duration,
            cut_start=voiceover.cut_start or 0.0,
            cut_end=voiceover.cut_end or 0.0,
            layer=voiceover.layer or 3,
        )


class VoiceoverRecord(ORMModel):
    """Raw format (``GET /projects/{id}``): JSON columns stay strings."""

    id: str
    project_id: str | None
    text: str | None
    text_with_pauses: str | None
    src: str | None
    start_time: Number | None
    timestamps: str | None
    duration: Number | None
    cut_start: Number | None
    cut_end: Number | None
    layer: Number | None


# --- requests -------------------------------------------------------------------


class CreateVoiceoverIn(RequestModel):
    start_time: float = 0.0


class DuplicateVoiceoverIn(RequestModel):
    """Falsy values (0, None) fall back to the source voiceover; ``layer`` defaults to 2."""

    start_time: Optional[float] = 0.0
    cut_start: Optional[float] = 0.0
    cut_end: Optional[float] = 0.0
    duration: Optional[float] = 0.0
    layer: Optional[int] = 2


class GenerateVoiceoverIn(RequestModel):
    text: str


class GenerateVoiceoverOut(BaseModel):
    message: str
    voiceover_id: str
    src: Any
    duration: Any
    timestamps: Any
