"""Data access for projects. Never commits; returns ORM objects."""

import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Project, Scene, SceneImage


async def list_with_thumbnails(session: AsyncSession) -> list[tuple[Project, str | None]]:
    """All projects, newest first, each with one non-empty scene image src (or None)."""
    thumbnail = (
        select(SceneImage.src)
        .join(Scene, Scene.id == SceneImage.scene_id)
        .where(Scene.project_id == Project.id)
        .where(SceneImage.src.is_not(None))
        .where(SceneImage.src != "")
        # NOTE: Scene.id is a random UUID, so "first" is effectively arbitrary.
        .order_by(Scene.id.asc(), SceneImage.id.asc())
        .limit(1)
        .correlate(Project)
        .scalar_subquery()
    )
    stmt = select(Project, thumbnail.label("thumbnail")).order_by(Project.created_at.desc())
    result = await session.execute(stmt)
    return [(project, thumb) for project, thumb in result.all()]


async def get_with_graph(session: AsyncSession, project_id: str) -> Project | None:
    """A project with scenes (+ images, characters, places), voiceovers and music loaded."""
    stmt = (
        select(Project)
        .where(Project.id == project_id)
        .options(
            selectinload(Project.scenes).selectinload(Scene.characters),
            selectinload(Project.scenes).selectinload(Scene.places),
            selectinload(Project.scenes).selectinload(Scene.images),
            selectinload(Project.places),
            selectinload(Project.characters),
            selectinload(Project.voiceovers),
            selectinload(Project.background_music),
        )
    )
    result = await session.execute(stmt)
    return result.scalars().first()


def add(session: AsyncSession, *, name: str, type: str | None = "BASIC", id: str | None = None) -> Project:
    project = Project(id=id if id is not None else str(uuid.uuid4()), name=name, type=type)
    session.add(project)
    return project


async def delete_by_id(session: AsyncSession, project_id: str) -> None:
    # Bulk delete: bypasses ORM cascades, children are left behind (audit B8).
    await session.execute(delete(Project).where(Project.id == project_id))
