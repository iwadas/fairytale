import uuid
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Table, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .config import Base

project_character_association = Table(
    "project_character_association",
    Base.metadata,
    Column("project_id", String(36), ForeignKey("projects.id")),
    Column("character_id", String(36), ForeignKey("characters.id"))
)

project_images_package_association = Table(
    "project_images_package_association",
    Base.metadata,
    Column("project_id", String(36), ForeignKey("projects.id")),
    Column("images_package_id", String(36), ForeignKey("images_packages.id"))
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

# ORM models
class Project(Base):
    __tablename__ = "projects"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    type = Column(String, nullable=True, default="BASIC")  # Add this line; adjust type/default as needed (e.g., String, Integer)
    scenes = relationship("Scene", back_populates="project")
    images_packages = relationship(
        "ImagesPackage",
        secondary=project_images_package_association,
        back_populates="projects"
    )
    characters = relationship(
        "Character",
        secondary=project_character_association,
        back_populates="projects"
    )
    voiceovers = relationship("Voiceover", back_populates="project")
    places = relationship(
        "Place", 
        secondary=place_project_association, 
        back_populates="projects"
    )
    background_music = relationship("Music", back_populates="project", uselist=False)


class Music(Base):
    __tablename__ = "music"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    project_id = Column(String(36), ForeignKey("projects.id"))
    project = relationship("Project", back_populates="background_music")
    name = Column(String, nullable=False)
    src = Column(String, nullable=True)
    start_time = Column(Float, nullable=False)
    duration = Column(Float, nullable=False)


class ImagesPackage(Base):
    __tablename__ = "images_packages"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    images = relationship("PhotoDumpImage", back_populates="package")
    projects = relationship(
        "Project",
        secondary=project_images_package_association,
        back_populates="images_packages"
    )

class PhotoDumpImage(Base):
    __tablename__ = "photo_dump_images"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    package_id = Column(String(36), ForeignKey("images_packages.id"), nullable=False, index=True)
    prompt = Column(Text, nullable=True)
    src = Column(String, nullable=True)
    package = relationship("ImagesPackage", back_populates="images")

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
    images = relationship("SceneImage", back_populates="scene", cascade="all, delete-orphan")
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
    prompt = Column(Text, nullable=True)
    src = Column(String, nullable=True)
    scene = relationship("Scene", back_populates="images")