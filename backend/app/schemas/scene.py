"""Scene and scene-image schemas (requests + both response formats)."""

from typing import Optional

from pydantic import BaseModel

from app.db.models import Scene, SceneImage
from app.schemas.character import CharacterOut, PlaceOut
from app.schemas.common import Number, ORMModel, loaded_list, RequestModel

# --- responses: serialized format ----------------------------------------------


class SceneImageOut(ORMModel):
    id: str | None
    time: str | None
    prompt: str | None
    src: str | None
    style: str | None
    idea: str | None

    @classmethod
    def from_model(cls, image: SceneImage) -> "SceneImageOut":
        return cls.model_validate(image)


class SceneOut(BaseModel):
    id: str
    project_id: str | None
    video_prompt: str | None
    video_src: str | None
    characters: list[CharacterOut]
    places: list[PlaceOut]
    images: list[SceneImageOut]
    start_time: Number | None
    duration: Number | None
    cut_start: Number
    cut_end: Number
    layer: Number

    @classmethod
    def from_model(cls, scene: Scene, *, with_images: bool = True) -> "SceneOut":
        images = loaded_list(scene, "images") if with_images else []
        return cls(
            id=scene.id,
            project_id=scene.project_id,
            video_prompt=scene.video_prompt,
            video_src=scene.video_src,
            characters=[CharacterOut.model_validate(c) for c in loaded_list(scene, "characters")],
            places=[PlaceOut.model_validate(p) for p in loaded_list(scene, "places")],
            images=[SceneImageOut.from_model(i) for i in images],
            start_time=scene.start_time,
            duration=scene.duration,
            cut_start=scene.cut_start or 0.0,
            cut_end=scene.cut_end or 0.0,
            layer=scene.layer or 2,
        )


# --- responses: raw format (GET /projects/{id}) ---------------------------------


class SceneImageRecord(ORMModel):
    id: str
    scene_id: str | None
    time: str | None
    prompt: str | None
    idea: str | None
    src: str | None
    style: str | None


class SceneRecord(ORMModel):
    id: str
    start_time: Number | None
    duration: Number | None
    video_prompt: str | None
    video_src: str | None
    project_id: str | None
    cut_start: Number | None
    cut_end: Number | None
    layer: Number | None
    images: list[SceneImageRecord]
    characters: list[CharacterOut]
    places: list[PlaceOut]


# --- requests -------------------------------------------------------------------


class CreateSceneIn(RequestModel):
    start_time: Optional[float] = 0.0


class DuplicateSceneIn(RequestModel):
    """Falsy values (0, None) fall back to the source scene; ``layer`` defaults to 2."""

    start_time: Optional[float] = 0.0
    cut_start: Optional[float] = 0.0
    cut_end: Optional[float] = 0.0
    duration: Optional[float] = 0.0
    layer: Optional[int] = 2


class GenerateImagePromptsIn(RequestModel):
    project_id: str
    selected_voiceover_text_part: str
    additional_info: Optional[str] = None


class FixImagePromptIn(RequestModel):
    scene_prompt: str
    style: Optional[str] = None
    style_power: Optional[float] = 0.5


class GenerateSceneVideoIn(RequestModel):
    prompt: str
    duration: int = 3


class FixVideoPromptIn(RequestModel):
    new_camera_movement: str
    additional_info: Optional[str] = None


class AddCharacterToSceneIn(RequestModel):
    scene_id: str
    character_id: str
