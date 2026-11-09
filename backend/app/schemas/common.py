"""Shared helpers for the API schemas.

Two wire formats exist for the same entities (kept byte-compatible for the
frontend):

* ``*Record`` models — the *raw* format of ``GET /projects`` and
  ``GET /projects/{id}``: every column as stored (JSON text columns stay
  strings, nullable columns stay ``None``).
* ``*Out`` models — the *serialized* format of create/duplicate/update
  responses: JSON text columns decoded, ``cut_*``/``layer`` falling back to
  defaults, unloaded relationships rendered as ``[]``.

Numeric columns are typed ``Number`` (``int | float``) so values pass through
unchanged (``Scene.duration`` is an Integer column holding floats too).
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator
from sqlalchemy import inspect

Number = int | float


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class RequestModel(BaseModel):
    """Request body whose explicit ``null`` fields behave as if omitted.

    Mirrors the former ``Body(default, embed=True)`` parameters: a ``null``
    value falls back to the field default (or is rejected as missing when the
    field is required).
    """

    @model_validator(mode="before")
    @classmethod
    def _null_means_default(cls, data: Any) -> Any:
        if isinstance(data, dict):
            return {key: value for key, value in data.items() if value is not None}
        return data


def is_loaded(obj: Any, attr: str) -> bool:
    """True when ``attr`` is loaded, i.e. reading it will not trigger lazy (async) IO."""
    return attr not in inspect(obj).unloaded


def loaded_list(obj: Any, attr: str) -> list[Any]:
    """The related objects if the relationship is loaded, otherwise ``[]``."""
    return list(getattr(obj, attr)) if is_loaded(obj, attr) else []
