"""Data access for the (single) settings row. Never commits; returns ORM objects.

Dict values are JSON-encoded into their Text columns.
"""

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Settings


def _encode(value: Any) -> Any:
    return json.dumps(value) if type(value) is dict else value


async def get(session: AsyncSession) -> Settings | None:
    result = await session.execute(select(Settings))
    return result.scalars().first()


def add(session: AsyncSession, **fields: Any) -> Settings:
    settings = Settings()
    apply(settings, **fields)
    session.add(settings)
    return settings


def apply(settings: Settings, **fields: Any) -> Settings:
    for key, value in fields.items():
        setattr(settings, key, _encode(value))
    return settings
