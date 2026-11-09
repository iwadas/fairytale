"""Characters and places as embedded in projects/scenes (same shape raw and serialized)."""

from app.schemas.common import ORMModel


class CharacterOut(ORMModel):
    id: str
    name: str | None
    prompt: str | None
    src: str | None


class PlaceOut(ORMModel):
    id: str
    name: str | None
    prompt: str | None
    src: str | None
