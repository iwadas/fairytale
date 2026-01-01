import uuid

from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Table, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

DATABASE_URL = "sqlite+aiosqlite:///./film.db"


# Async engine
engine = create_async_engine(DATABASE_URL, echo=True, future=True)

# Session factory
async_session_maker = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

# Association tables
project_character_association = Table(
    "project_character_association",
    Base.metadata,
    Column("project_id", String(36), ForeignKey("projects.id")),
    Column("character_id", String(36), ForeignKey("characters.id"))
)

scene_character_association = Table(
    "scene_character_association",
    Base.metadata,
    Column("scene_id", String(36), ForeignKey("scenes.id")),
    Column("character_id", String(36), ForeignKey("characters.id"))
)

place_project_association = Table(
    "project_places",
    Base.metadata,
    Column("project_id", String(36), ForeignKey("projects.id"), primary_key=True),
    Column("place_id", String(36), ForeignKey("places.id"), primary_key=True),
)

place_scene_association = Table(
    "scene_places",
    Base.metadata,
    Column("scene_id", String(36), ForeignKey("scenes.id"), primary_key=True),
    Column("place_id", String(36), ForeignKey("places.id"), primary_key=True),
)

async def get_session() -> AsyncSession:
    async with async_session_maker() as session:
        yield session

# ORM models
class Project(Base):
    __tablename__ = "projects"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    scenes = relationship("Scene", back_populates="project")
    characters = relationship(
        "Character",
        secondary=project_character_association,
        back_populates="projects"
    )
    voiceovers = relationship("Voiceover", back_populates="project")
    places = relationship("Place", secondary=place_project_association, back_populates="projects")

class Voiceover(Base):
    __tablename__ = "voiceovers"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    project_id = Column(String(36), ForeignKey("projects.id"))
    project = relationship("Project", back_populates="voiceovers")
    text = Column(Text, nullable=True)
    text_with_pauses = Column(Text, nullable=True)
    src = Column(String, nullable=True)
    start_time = Column(Float, nullable=False)
    timestamps = Column(Text, nullable=True)
    duration = Column(Float, nullable=True)

class Scene(Base):
    __tablename__ = "scenes"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    start_time = Column(Float, nullable=True)
    duration = Column(Integer, nullable=True)
    video_prompt = Column(Text, nullable=True)
    video_src = Column(String, nullable=True)
    project_id = Column(String(36), ForeignKey("projects.id"))
    project = relationship("Project", back_populates="scenes")
    images = relationship("SceneImage", back_populates="scene")
    characters = relationship(
        "Character",
        secondary=scene_character_association,
        back_populates="scenes"
    )
    places = relationship("Place", secondary=place_scene_association, back_populates="scenes")

class Place(Base):
    __tablename__ = "places"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    prompt = Column(String, nullable=False)
    src = Column(String, nullable=True)
    projects = relationship("Project", secondary=place_project_association, back_populates="places")
    scenes = relationship("Scene", secondary=place_scene_association, back_populates="places")

class Character(Base):
    __tablename__ = "characters"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    name = Column(String, nullable=False)
    prompt = Column(Text, nullable=True)
    src = Column(String, nullable=True)
    projects = relationship(
        "Project",
        secondary=project_character_association,
        back_populates="characters"
    )
    scenes = relationship(
        "Scene",
        secondary=scene_character_association,
        back_populates="characters"
    )

class SceneImage(Base):
    __tablename__ = "scene_images"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scene_id = Column(String(36), ForeignKey("scenes.id"), nullable=False, index=True)
    time = Column(String(20), nullable=False, default="start")
    prompt = Column(Text, nullable=False)
    src = Column(String, nullable=False)
    scene = relationship("Scene", back_populates="images")
