from typing import Any, List, Optional
import uuid
from requests import session
from sqlalchemy import select, delete
from .models import Project, Voiceover, Place, Scene, Character, ImagesPackage
from .decorators import with_session # Import your new tool
from sqlalchemy.orm import selectinload
from .serialization import serialize_project, serialize_voiceover, serialize_scene
import json

# PROJECTS
@with_session
async def get_projects_db(session=None):
    stmt = select(Project).order_by(Project.created_at.desc())
    result = await session.execute(stmt)
    return result.scalars().all()

@with_session
async def get_project_db(id: str, serialize: bool=False, session=None):
    stmt = (
        select(Project)
        .where(Project.id == id)
        .options(
            selectinload(Project.scenes)
                .selectinload(Scene.characters),
            selectinload(Project.scenes)
                .selectinload(Scene.places),
            selectinload(Project.scenes)
                .selectinload(Scene.images),
            selectinload(Project.places),
            selectinload(Project.characters),
            selectinload(Project.voiceovers),
            selectinload(Project.images_packages)
                .selectinload(ImagesPackage.images)
        )
    )
    
    result = await session.execute(stmt)
    project_orm = result.scalars().first()
    if serialize and project_orm:
        return serialize_project(project_orm)
    else:
        return project_orm
    
@with_session
async def create_project_db(name: str = "", type: str = "BASIC", session=None):
    new_project = Project(name=name, type=type)
    session.add(new_project)
    return serialize_project(new_project)

@with_session
async def remove_project_db(id: str, session=None):
    stmt = delete(Project).where(Project.id == id)
    await session.execute(stmt)
    return {"message": "Project deleted successfully"}

@with_session
async def copy_project_db(
    source_project: dict, 
    suffix: str = " (Copy)", 
    session=None
) -> str:
    new_project = Project(
        id=str(uuid.uuid4()),
        name=f"{source_project['name']}"+suffix,  # You can customize the name
        type=source_project.get("type", "BASIC")  # Copy type if exists, else default
    )
    session.add(new_project)

    # 3. Maps to keep track of old → new object relationships
    character_old_to_new = {}
    place_old_to_new = {}

    # 4. Copy Characters (if any)
    for orig_char in source_project["characters"]:
        new_char = Character(
            id=str(uuid.uuid4()),
            name=orig_char["name"],
            prompt=orig_char["prompt"],
            src=orig_char["image_url"],
        )
        session.add(new_char)
        new_project.characters.append(new_char)
        character_old_to_new[orig_char.id] = new_char

    # 5. Copy Places (if any)
    for orig_place in source_project["places"]:
        new_place = Place(
            id=str(uuid.uuid4()),
            name=orig_place["name"],
            prompt=orig_place["prompt"],
            src=orig_place["image_url"],
        )
        session.add(new_place)
        new_project.places.append(new_place)
        place_old_to_new[orig_place.id] = new_place

    # 6. Copy Scenes + their relationships
    for orig_scene in source_project["scenes"]:
        new_scene = Scene(
            id=str(uuid.uuid4()),
            duration=orig_scene["duration"],
            start_time=orig_scene["start_time"],
            video_prompt=orig_scene["video_prompt"],
            video_src=orig_scene["video_src"]
        )
        session.add(new_scene)
        new_project.scenes.append(new_scene)

        # Re-link characters
        for orig_char in orig_scene["characters"]:
            if orig_char.id in character_old_to_new:
                new_scene.characters.append(character_old_to_new[orig_char["id"]])

        # Re-link places (if scene has places)
        for orig_place in orig_scene["places"]:
            if orig_place.id in place_old_to_new:
                new_scene.places.append(place_old_to_new[orig_place["id"]])

    # 7. Copy Voiceovers
    for orig_vo in source_project["voiceovers"]:
        new_vo = Voiceover(
            id=str(uuid.uuid4()),
            text=orig_vo["text"],
            text_with_pauses=orig_vo["text_with_pauses"],
            start_time=orig_vo["start_time"],
            duration=orig_vo["duration"],
            timestamps=json.dumps(orig_vo["timestamps"]), 
            src=orig_vo["src"]
        )
        session.add(new_vo)
        new_project.voiceovers.append(new_vo)

    return serialize_project(new_project)

# PHOTO DUMP PROJECTS
@with_session
async def update_pd_project_db(
    id: str, 
    name: str, 
    images_packages_ids: List[str], 
    session=None
):
    stmt = select(Project).where(Project.id == id)
    result = await session.execute(stmt)
    project = result.scalars().first()
    if project:
        project.name = name
        project.images_packages = []  # Clear existing associations
        # add new associations
        for package_id in images_packages_ids:
            images_package = await session.get(ImagesPackage, package_id)
            if images_package:
                project.images_packages.append(images_package)

        session.add(project)
        return serialize_project(project)
    else:
        return None


# VOICEOVERS
@with_session
async def update_voiceover_db(id: str, session=None, **kwargs):
    stmt = select(Voiceover).where(Voiceover.id == id)
    result = await session.execute(stmt)
    voiceover = result.scalars().first()
    if voiceover:
        for key, value in kwargs.items():
            setattr(voiceover, key, value)
        session.add(voiceover)
        return serialize_voiceover(voiceover)
    else:
        return None
    
async def create_voiceover_db(
        id: Optional[str] = None, 
        project_id: str = "", 
        text: str = "", 
        start_time: float = 0.0, 
        timestamps: Optional[Any] = None, 
        text_with_pauses: Optional[str] = None,
        duration: Optional[float] = None,
        session=None
    ):

    if id is None:
        id = str(uuid.uuid4())
    if text is None:
        raise ValueError("Text cannot be None")
    if project_id is None:
        raise ValueError("Project ID cannot be None")

    # check if timestamps is json / string and convert to string if needed
    if timestamps is not None and not isinstance(timestamps, str):
        timestamps = json.dumps(timestamps)

    new_vo = Voiceover(id=id, project_id=project_id, text=text, start_time=start_time, timestamps=timestamps, text_with_pauses=text_with_pauses, duration=duration)
    session.add(new_vo)
    return serialize_voiceover(new_vo)

# SCENES
@with_session
async def create_scene_db(
    project_id: str,
    duration: Optional[float] = 0.0,
    start_time: Optional[float] = 0.0,
    session=None, 
):
    new_scene = Scene(
        project_id=project_id, 
        duration=duration, 
        start_time=start_time
    )
    session.add(new_scene)
    return serialize_scene(new_scene)


async def update_scene_db(id: str, session=None, **kwargs):
    stmt = select(Scene).where(Scene.id == id)
    result = await session.execute(stmt)
    scene = result.scalars().first()
    if scene:
        for key, value in kwargs.items():
            setattr(scene, key, value)
        session.add(scene)
        return serialize_scene(scene)
    else:
        return None
