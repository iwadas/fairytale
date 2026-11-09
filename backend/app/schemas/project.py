"""Project schemas (requests + both response formats)."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, field_serializer

from app.db.models import Project
from app.schemas.character import CharacterOut, PlaceOut
from app.schemas.common import ORMModel, loaded_list
from app.schemas.music import MusicOut, MusicRecord
from app.schemas.scene import SceneOut, SceneRecord
from app.schemas.voiceover import VoiceoverOut, VoiceoverRecord

# --- responses: raw format --------------------------------------------------------


def _isoformat(value: datetime | None) -> str | None:
    # Same as the former jsonable_encoder output (datetime.isoformat()).
    return value.isoformat() if value is not None else None


class ProjectListItem(BaseModel):
    """An entry of ``GET /projects``."""

    id: str
    name: str | None
    created_at: datetime | None
    type: str | None
    thumbnail: str | None

    _serialize_created_at = field_serializer("created_at", when_used="json")(_isoformat)

    @classmethod
    def from_model(cls, project: Project, thumbnail: str | None) -> "ProjectListItem":
        return cls(
            id=project.id,
            name=project.name,
            created_at=project.created_at,
            type=project.type,
            thumbnail=thumbnail,
        )


class ProjectRecord(ORMModel):
    """``GET /projects/{id}``: the full graph with raw column values."""

    id: str
    name: str | None
    created_at: datetime | None
    type: str | None
    scenes: list[SceneRecord]
    places: list[PlaceOut]
    characters: list[CharacterOut]
    voiceovers: list[VoiceoverRecord]
    background_music: list[MusicRecord]

    _serialize_created_at = field_serializer("created_at", when_used="json")(_isoformat)


# --- responses: serialized format -----------------------------------------------


class ProjectOut(BaseModel):
    """Serialized project; ``model_dump()`` of it is what ``VideoBuilder`` consumes."""

    id: str
    name: str | None
    created_at: str | None
    type: str | None
    characters: list[CharacterOut]
    places: list[PlaceOut]
    scenes: list[SceneOut]
    voiceovers: list[VoiceoverOut]
    background_music: list[MusicOut]

    @classmethod
    def from_model(cls, project: Project) -> "ProjectOut":
        return cls(
            id=project.id,
            name=project.name,
            created_at=project.created_at.isoformat() if project.created_at else None,
            type=project.type,
            characters=[CharacterOut.model_validate(c) for c in loaded_list(project, "characters")],
            places=[PlaceOut.model_validate(p) for p in loaded_list(project, "places")],
            scenes=[SceneOut.from_model(s) for s in loaded_list(project, "scenes")],
            voiceovers=[VoiceoverOut.from_model(v) for v in loaded_list(project, "voiceovers")],
            background_music=[MusicOut.from_model(m) for m in loaded_list(project, "background_music")],
        )


class CreateProjectOut(BaseModel):
    message: str
    project_id: str


class CopyProjectOut(BaseModel):
    success: bool
    new_project_id: str
    message: str


# --- requests -------------------------------------------------------------------


class ScriptIn(BaseModel):
    # NOTE: the Optional fields have no default, so Pydantic v2 treats them as
    # required (nullable). Kept as-is: the frontend always sends every key.
    topic: str
    duration: int
    description: Optional[str]
    data: Optional[str]
    gather_data: bool
    persistant_characters: bool
    reference_stories: Optional[str]


class ScriptsOut(BaseModel):
    scripts: list[Any]


class ProjectIn(BaseModel):
    topic: str
    script: str


class TimelineUpdateIn(BaseModel):
    """``PUT /projects/{id}``: timeline elements as sent by the editor.

    Each element is a dict with ``id`` and ``type`` (``scene`` | ``voiceover`` |
    ``music``) plus timing fields; see ``project_service.update_timeline``.
    """

    timeline_elements: list
