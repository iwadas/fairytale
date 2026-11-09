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

from pydantic import BaseModel, ConfigDict
from sqlalchemy import inspect

Number = int | float


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


def is_loaded(obj: Any, attr: str) -> bool:
    """True when ``attr`` is loaded, i.e. reading it will not trigger lazy (async) IO."""
    return attr not in inspect(obj).unloaded


def loaded_list(obj: Any, attr: str) -> list[Any]:
    """The related objects if the relationship is loaded, otherwise ``[]``."""
    return list(getattr(obj, attr)) if is_loaded(obj, attr) else []
