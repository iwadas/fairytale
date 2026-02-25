from typing import Any, Dict, List, Optional
import uuid
from requests import session
from sqlalchemy import select, delete, func
from .models import PhotoDumpImage, Project, SceneImage, Voiceover, Place, Scene, Character, ImagesPackage, Music, project_images_package_association
from .decorators import with_session # Import your new tool
from sqlalchemy.orm import selectinload
from .serialization import serialize_music, serialize_project, serialize_scene_image, serialize_voiceover, serialize_scene
import json

# PROJECTS
@with_session
async def get_projects_db(with_thumbnails=False, session=None):
    if with_thumbnails:
        # 1. Create a subquery that fetches exactly ONE valid image src per project
        scene_image_subq = (
            select(SceneImage.src)
            .join(Scene, Scene.id == SceneImage.scene_id)
            # Link the subquery to the outer Project query
            .where(Scene.project_id == Project.id)
            # Ensure it actually has a src, as requested
            .where(SceneImage.src.is_not(None))
            .where(SceneImage.src != "")
            # Order by whatever determines your "first" scene/image (adjust if needed)
            .order_by(Scene.id.asc(), SceneImage.id.asc()) 
            .limit(1)
            .correlate(Project) # Tells SQLAlchemy this relies on the outer Project query
            .scalar_subquery()
        )

        photo_dump_subq = (
            select(PhotoDumpImage.src)
            .join(
                project_images_package_association,
                project_images_package_association.c.images_package_id == PhotoDumpImage.package_id
            )
            # Link the subquery to the outer Project query
            .where(project_images_package_association.c.project_id == Project.id)
            .where(PhotoDumpImage.src.is_not(None))
            .where(PhotoDumpImage.src != "")
            # Order randomly to pick a random image from the package
            .order_by(func.random()) 
            .limit(1)
            .correlate(Project)
            .scalar_subquery()
        )

        # 2. Select the Project AND our new subquery as a labeled column
        stmt = (
            select(
                Project, 
                func.coalesce(scene_image_subq, photo_dump_subq).label('thumbnail')
            )
            .order_by(Project.created_at.desc())
        )
        
        result = await session.execute(stmt)
        
        # 3. Attach the thumbnail dynamically to the project object for easy access
        projects = []
        for project, thumbnail in result.all():
            # project.thumbnail will be the string 'src' or None
            project.thumbnail = thumbnail 
            projects.append(project)
            
        return projects

    else:
        # Standard query without thumbnails
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
            selectinload(Project.background_music),
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
async def create_project_db(id: Optional[str] = None, name: str = "", type: str = "BASIC", session=None):
    if id is None:
        id = str(uuid.uuid4())
    new_project = Project(id=id, name=name, type=type)
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
            if(key == "timestamps" and isinstance(value, list)):
                value = json.dumps(value)

            setattr(voiceover, key, value)
        session.add(voiceover)
        return serialize_voiceover(voiceover)
    else:
        return None

@with_session
async def get_project_voiceovers_db(project_id: str, session=None):
    stmt = select(Voiceover).where(Voiceover.project_id == project_id)
    result = await session.execute(stmt)
    voiceovers = result.scalars().all()
    return [serialize_voiceover(vo) for vo in voiceovers]

@with_session
async def get_voiceover_db(id: str, session=None):
    stmt = select(Voiceover).where(Voiceover.id == id)
    result = await session.execute(stmt)
    voiceover = result.scalars().first()
    if voiceover:
        return serialize_voiceover(voiceover)
    else:
        return None

@with_session
async def remove_voiceover_db(id: str, session=None):
    stmt = delete(Voiceover).where(Voiceover.id == id)
    await session.execute(stmt)
    return {"message": "Voiceover deleted successfully"}
    
@with_session
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
async def get_scene_db(id: str, session=None):
    stmt = (
        select(Scene)
        .where(Scene.id == id)
        .options(
            selectinload(Scene.images)
        )
    )
    result = await session.execute(stmt)
    scene = result.scalars().first()
    if scene:
        return serialize_scene(scene)
    else:
        return None


@with_session
async def create_scene_db(
    project_id: str,
    scene_id: Optional[str] = None,
    duration: Optional[float] = 0.0,
    start_time: Optional[float] = 0.0,
    video_prompt: Optional[str] = None,
    session=None, 
    images: Optional[List[Dict[str, Any]]] = None,
):
    if scene_id is None:
        scene_id = str(uuid.uuid4())

    new_scene = Scene(
        id=scene_id,
        project_id=project_id, 
        duration=duration, 
        start_time=start_time,
        video_prompt=video_prompt
    )
    session.add(new_scene)

    if images:
        for img in images:
            new_image = SceneImage(
                scene_id=scene_id,
                prompt=img.get("prompt", ""),
                time=img.get("time", "start"),
            )
            session.add(new_image)


    return serialize_scene(new_scene)

@with_session
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
    
@with_session
async def remove_scene_db(id: str, session=None):
    stmt = delete(Scene).where(Scene.id == id)
    await session.execute(stmt)
    return {"message": "Scene deleted successfully"}


# SCENE IMAGES
@with_session
async def remove_scene_image_db(id: str, session=None):
    stmt = delete(SceneImage).where(SceneImage.id == id)
    await session.execute(stmt)
    return {"message": "Scene image deleted successfully"}

@with_session
async def create_or_update_scene_image_db(id: Optional[str] = None, scene_id: Optional[str] = None, src: str = "", prompt: Optional[str] = None, time: Optional[str] = "start", session=None):
    if not scene_id:
        raise ValueError("scene_id is required")

    if id is not None:
        # Update existing scene image
        stmt = select(SceneImage).where(SceneImage.id == id)
        result = await session.execute(stmt)
        scene_image = result.scalars().first()
        if src:
            scene_image.src = src
        if prompt is not None:
            scene_image.prompt = prompt
        scene_image.time = time
        session.add(scene_image)
    else:
        # Create new scene image
        scene_image = SceneImage(
            id=str(uuid.uuid4()),
            scene_id=scene_id,
            src=src,
            prompt=prompt,
            time=time
        )
        session.add(scene_image)

    return serialize_scene_image(scene_image)

@with_session
async def create_music_db(project_id: str, session=None):
    new_music = Music(
        id=str(uuid.uuid4()),
        project_id=project_id,
        name="",
        src="",
        start_time=0.0,
        duration=30.0
    )
    session.add(new_music)
    return serialize_music(new_music)

@with_session
async def get_music_db(id: str, session=None):
    stmt = select(Music).where(Music.id == id)
    result = await session.execute(stmt)
    music = result.scalars().first()
    if music:
        return serialize_music(music)
    else:
        return None
    
@with_session
async def update_music_db(id: str, session=None, **kwargs):
    stmt = select(Music).where(Music.id == id)
    result = await session.execute(stmt)
    music = result.scalars().first()
    if music:
        for key, value in kwargs.items():
            setattr(music, key, value)
        session.add(music)
        return serialize_music(music)
    else:
        return None