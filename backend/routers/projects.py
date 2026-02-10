import json
from fastapi import APIRouter, HTTPException, Body, Depends
from AI.tts import TTS
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete, desc, inspect
from sqlalchemy.orm import selectinload

import uuid
from sqlalchemy.sql import func
from datetime import datetime
from copy import deepcopy

import os
from typing import List, Dict, Optional, Tuple, Set, Any
from db import get_session, Project, Scene, Voiceover, Place, Character, ImagesPackage, PhotoDumpImage
from schemas import ProjectBasicOutput, ProjectOutput
from .translations import get_translated_voiceovers
from moviepy import VideoFileClip, concatenate_videoclips, AudioFileClip, CompositeAudioClip
from generate import generate_mp4
from generate_photo_dump import generate_photo_dump_mp4
from services import generate_speech, filename_from_name
from database.crud import create_voiceover_db, get_projects_db, get_project_db, remove_project_db, update_voiceover_db, update_scene_db, update_pd_project_db, create_project_db, copy_project_db

import re

router = APIRouter(prefix="/projects", tags=["projects"])

def get_save_name(name):
        name = re.sub(r'[\\/:*?"<>|]', '', name)
        # optionally replace spaces with underscores
        name = name.replace(" ", "_")
        return name

@router.get("")
async def projects():
    projects = await get_projects_db()
    return projects

@router.get("/{project_id}")
async def project(
        project_id: str, 
    ):
    return await get_project_db(id=project_id)

@router.delete("/{project_id}")
async def delete_project(project_id: str):
    await remove_project_db(id=project_id)
    return {"message": "Project deleted successfully"}

@router.put("/{project_id}")
async def update_project(
    scenes: list = Body(...),
    voiceovers: list = Body(...),
):
    # === Load current scenes (only scalar fields for diff) ===
    for scene in scenes:
        await update_scene_db(
            id=scene["id"],
            start_time=scene["start_time"],
            duration=scene["duration"],
        )
        
    for vo in voiceovers:
        await update_voiceover_db(
            id=vo["id"],
            text=vo["text"],
            start_time=vo["start_time"],
            duration=vo["duration"],
            text_with_pauses=vo.get("text_with_pauses", "")
        )
    
    return {"message": "Update successful"}


@router.post("/download/{project_id}")
async def download_project(project_id: str):
    project = await get_project_db(id=project_id, serialize=True)

    output_dir = "videos"
    os.makedirs(output_dir, exist_ok=True)
    output_filename = f"{get_save_name(project['name'])}.mp4"
    output_path = os.path.join(output_dir, output_filename)
    print("starting generation")
    generate_mp4(project, output_path)

    return {"message": "success"}


@router.post("/download-pd/{project_id}")
async def download_photo_dump_project(
    project_id: str,
):
    project = await get_project_db(id=project_id, serialize=True)
    images = []
    for images_package in project["images_packages"]:
        images.extend([img for img in images_package["images"] if img["src"] is not None])

    voiceover = project["voiceovers"][0] if project["voiceovers"] else None
    generate_photo_dump_mp4(
        images=images,
        title=get_save_name(project["name"]),
        voiceover=voiceover
    )
    return {"message": "success"}
    

@router.put("/photo-dump/{project_id}")
async def update_photo_dump_project(
    project_id: str,
    name: str = Body(...),
    images_packages_ids: List[str] = Body(...),
):
    await update_pd_project_db(id=project_id, name=name, images_packages_ids=images_packages_ids)
    return {"message": "Photo Dump Project updated successfully"}

@router.post("/download-photo-dump")
async def download_photo_dump_project(
    title: str = Body(..., embed=True),
    story: str = Body(..., embed=True),
    images_package_ids: List[str] = Body(..., embed=True),
):
    # get all images from packages
    # GENERATE VOICEOVER
    project = await create_project_db(
        name = f"{title} (Photo Dump)",
    )
    project_id = project["id"]

    voiceover = TTS(
        provider="camb",
        text=story,
        project_id=project_id
    )
    await create_voiceover_db(**voiceover)
    
    await update_pd_project_db(id=project_id, name=f"{title} (Photo Dump)", images_packages_ids=images_package_ids)

    return {"message": "success"}


# TODO
@router.post("/add-translations/{project_id}")
async def add_translations(
    project_id: str,
    session: AsyncSession = Depends(get_session)
):
    return
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
):
    # 1. Fetch the original project with all relationships
    source_project = await get_project_db(id=project_id, serialize=True)
    new_project = await copy_project_db(source_project=source_project, suffix=" (Copy)")
    
    return {
        "success": True,
        "new_project_id": new_project["id"],
        "message": "Project copied successfully"
    }