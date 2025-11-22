from fastapi import APIRouter, HTTPException, Body, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from sqlalchemy.orm import selectinload
import uuid
from sqlalchemy.sql import func
from datetime import datetime
from copy import deepcopy

import os
from typing import List, Dict, Tuple, Set, Any
from db import get_session, Project, Scene, Voiceover, Place, Character
from schemas import ProjectBasicOutput, ProjectOutput
from .translations import get_translated_voiceovers
from moviepy import VideoFileClip, concatenate_videoclips, AudioFileClip, CompositeAudioClip
from generate import generate_mp4


import re

router = APIRouter(prefix="/projects", tags=["projects"])

@router.post("/download/{project_id}")
async def download_project(project_id: str, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Project)
        .where(Project.id == project_id)
        .options(
            selectinload(Project.scenes)
                .selectinload(Scene.characters),
            selectinload(Project.scenes)
                .selectinload(Scene.places),
            selectinload(Project.places),
            selectinload(Project.characters),
            selectinload(Project.voiceovers),
        )
    )
    project_orm = result.scalars().first()
    if not project_orm:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # project in python - dicts, lists, etc
    project = serialize_project(project_orm)

    def get_save_name(name):
        name = re.sub(r'[\\/:*?"<>|]', '', name)
        # optionally replace spaces with underscores
        name = name.replace(" ", "_")
        return name

    output_dir = "videos"
    os.makedirs(output_dir, exist_ok=True)
    output_filename = f"{get_save_name(project["name"])}.mp4"
    output_path = os.path.join(output_dir, output_filename)
    print("starting generation")
    generate_mp4(project, output_path)

    return {"message": "success"}




@router.post("/add-scene/{project_id}")
async def add_scene_to_project(
    project_id: str,
    scene_number: int = Body(...),
    image_prompt: str = Body(...),
    video_prompt: str = Body(...),
    duration: int = Body(...),
    session: AsyncSession = Depends(get_session)
):
    return
    
    # ADD + 1 TO ALL SCENES >= scene_number
    project = await session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await session.execute(
            update(Scene)
            .where(Scene.project_id == project_id)
            .where(Scene.scene_number >= scene_number)
            .values(scene_number=Scene.scene_number + 1)
        )

    new_scene = Scene(
        id=str(uuid.uuid4()),
        scene_number=scene_number,
        image_prompt=image_prompt if image_prompt else "None",
        video_prompt=video_prompt if video_prompt else "None",
        duration=duration if duration else 5,
        project_id=project_id
    )
    session.add(new_scene)
    await session.commit()
    await session.refresh(new_scene)
    return {
        "message": f"New scene: {new_scene.id} added to project {project_id}",
        "scene": new_scene
    }


 

@router.post("")
async def create_project(name: str = Body(...), session: AsyncSession = Depends(get_session)):
    return
    new_project = Project(id=str(uuid.uuid4()), name=name)
    session.add(new_project)
    await session.commit()
    await session.refresh(new_project)
    return {"project_id": new_project.id}

@router.delete("/{project_id}")
async def delete_project(project_id: str, session: AsyncSession = Depends(get_session)):
    project = await session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await session.delete(project)
    await session.commit()
    return {"message": f"Project {project_id} deleted"}

@router.get("")
async def list_projects(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Project))
    projects = result.scalars().all()
    return [ProjectBasicOutput.model_validate(p).model_dump() for p in projects]


@router.post("/add-translations/{project_id}")
async def add_translations(
    project_id: str,
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(Project)
        .where(Project.id == project_id)
        .options(
            selectinload(Project.scenes).selectinload(Scene.characters),
            selectinload(Project.scenes).selectinload(Scene.places),
            selectinload(Project.places),
            selectinload(Project.characters),
            selectinload(Project.voiceovers),
        )
    )
    if not result:
        raise HTTPException(status_code=404, detail="Project not found")
        
    source_project = serialize_project(result.scalars().first())
    
    language_index = 0
    while True:
        translated_voiceovers = get_translated_voiceovers(language_index, source_project["voiceovers"])
        if translated_voiceovers == None:
            break
        
        translated_source_project = deepcopy(source_project)
        translated_source_project["voiceovers"] = translated_voiceovers
        

        await db_copy_project(source_project=translated_source_project, suffix=f" (PL)", session=session)
        language_index += 1
    
    return {"message": "success"}




    
@router.post("/copy/{project_id}")
async def copy_project(
    project_id: str,
    session: AsyncSession = Depends(get_session)
):
    # 1. Fetch the original project with all relationships
    result = await session.execute(
        select(Project)
        .where(Project.id == project_id)
        .options(
            selectinload(Project.scenes).selectinload(Scene.characters),
            selectinload(Project.scenes).selectinload(Scene.places),
            selectinload(Project.places),
            selectinload(Project.characters),
            selectinload(Project.voiceovers),
        )
    )
    if not source_project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    source_project = serialize_project(result.scalars().first())
    new_project_id = await db_copy_project(source_project=source_project, suffix=" (Copy)", session=session)
    
    return {
        "success": True,
        "new_project_id": new_project_id,
        "message": "Project copied successfully"
    }


def _to_dict(obj: Any, visited: set | None = None) -> Any:
    if visited is None:
        visited = set()

    if obj is None:
        return None

    # Handle lists/sets/tuples
    if isinstance(obj, (list, tuple, set)):
        return [_to_dict(item, visited) for item in obj]

    obj_id = id(obj)
    if obj_id in visited:
        return None  # or {"__ref__": str(obj_id)} if you want to debug
    visited.add(obj_id)

    # Skip non-ORM objects early
    if not hasattr(obj, "__table__") and not hasattr(obj, "__mapper__"):
        # Handle primitives
        if isinstance(obj, (str, int, float, bool, uuid.UUID)):
            return obj
        if isinstance(obj, datetime):
            return obj.isoformat()
        return str(obj)

    data: dict[str, Any] = {}

    # 1. Copy scalar columns
    for col in obj.__table__.columns:
        val = getattr(obj, col.name)
        if isinstance(val, datetime):
            data[col.name] = val.isoformat()
        elif isinstance(val, uuid.UUID):
            data[col.name] = str(val)
        else:
            data[col.name] = val

    # 2. Copy relationships (without double-list)
    for name, rel in obj.__mapper__.relationships.items():
        related_objs = getattr(obj, name)

        if related_objs is None:
            data[name] = None
        elif rel.uselist:
            # related_objs is already a list → just recurse
            data[name] = [_to_dict(item, visited) for item in related_objs]
        else:
            # to-one
            data[name] = _to_dict(related_objs, visited)

    return data


def serialize_project(project_orm) -> dict | None:
    if project_orm is None:
        return None
    if not hasattr(project_orm, "__table__"):
        raise TypeError(f"Expected ORM instance, got {type(project_orm)}")
    return _to_dict(project_orm)

async def db_copy_project(source_project=None, suffix=" (Copy)", session=None):
    new_project = Project(
        id=str(uuid.uuid4()),
        name=f"{source_project["name"]}"+suffix,  # You can customize the name
        created_at=func.now()
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
            image_prompt=orig_scene["image_prompt"],
            video_prompt=orig_scene["video_prompt"],
            image_src=orig_scene["image_src"],
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
            timestamps=orig_vo["timestamps"], 
            src=orig_vo["src"]
        )
        session.add(new_vo)
        new_project.voiceovers.append(new_vo)

    # 8. Commit everything
    await session.commit()

    return new_project.id

@router.get("/{project_id}")
async def get_project(project_id: str, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Project)
        .where(Project.id == project_id)
        .options(
            selectinload(Project.scenes)
                .selectinload(Scene.characters),
            selectinload(Project.scenes)
                .selectinload(Scene.places),
            selectinload(Project.places),
            selectinload(Project.characters),
            selectinload(Project.voiceovers),
        )
    )
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    # serialize with Pydantic
    return project


def diff_by_id(
    old: List[Dict],
    new: List[Dict],
) -> Tuple[Set[str], List[Dict], List[Dict]]:
    """
    Returns:
        deleted_ids: set of ids that exist in old but not in new
        to_insert:   rows that are in new but not in old (no id match)
        to_update:   rows that exist in both but have different values
    """
    old_map = {item["id"]: item for item in old}
    new_map = {item["id"]: item for item in new}

    deleted = old_map.keys() - new_map.keys()

    to_insert = []
    to_update = []

    for nid, nitem in new_map.items():
        if nid not in old_map:
            to_insert.append(nitem)
        else:
            oitem = old_map[nid]
            # deep comparison – ignore keys that are always generated (e.g. src after generation)
            if oitem != nitem:
                to_update.append(nitem)

    return deleted, to_insert, to_update

@router.put("/{project_id}")
async def update_project(
    project_id: str,
    scenes: list = Body(...),
    voiceovers: list = Body(...),
    session: AsyncSession = Depends(get_session)
):
    # === Load current scenes (only scalar fields for diff) ===
    result = await session.execute(
        select(Scene).where(Scene.project_id == project_id)
    )
    cur_scenes = result.scalars().all()

    cur_scenes_dict = [
        {
            "id": s.id,
            "project_id": s.project_id,
            "image_prompt": s.image_prompt,
            "image_src": s.image_src,
            "start_time": s.start_time,
            "duration": s.duration,
            "video_prompt": s.video_prompt,
            "video_src": s.video_src,
        }
        for s in cur_scenes
    ]

    # === Load voiceovers ===
    result = await session.execute(
        select(Voiceover).where(Voiceover.project_id == project_id)
    )
    cur_voiceovers = result.scalars().all()
    cur_voiceovers_dict = [v.__dict__ for v in cur_voiceovers]

    # === Diff ===
    del_sc_ids, ins_sc, upd_sc = diff_by_id(cur_scenes_dict, scenes)
    del_vo_ids, ins_vo, upd_vo = diff_by_id(cur_voiceovers_dict, voiceovers)

    # === DELETE ===
    if del_sc_ids:
        await session.execute(
            delete(Scene).where(Scene.id.in_(del_sc_ids))
        )

    if del_vo_ids:
        await session.execute(
            delete(Voiceover).where(Voiceover.id.in_(del_vo_ids))
        )

    # === INSERT SCENES (only scalar fields) ===
    if ins_sc:
        new_scenes = []
        for row in ins_sc:
            # Remove relationship fields
            row.pop("characters", None)
            row.pop("places", None)
            new_scenes.append(Scene(**row, project_id=project_id))
        session.add_all(new_scenes)

    # === UPDATE SCENES (only scalar fields) ===
    if upd_sc:
        for row in upd_sc:
            # Remove relationship fields
            row.pop("characters", None)
            row.pop("places", None)
            # Create minimal Scene instance with only scalar fields
            scene = Scene(**row)
            await session.merge(scene)  # Safe: no relationships touched

    # === VOICEOVERS (no relationships) ===
    if ins_vo:
        session.add_all([Voiceover(**row, project_id=project_id) for row in ins_vo])

    if upd_vo:
        for row in upd_vo:
            await session.merge(Voiceover(**row))

    await session.commit()

    return {
        "updated": len(upd_sc) + len(upd_vo),
        "inserted": len(ins_sc) + len(ins_vo),
        "deleted": len(del_sc_ids) + len(del_vo_ids),
    }