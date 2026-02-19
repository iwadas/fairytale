from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from AI.tts import TTS
from AI.llm import LLM
from script.generate_scenes import generate_scenes, split_script

import uuid
from copy import deepcopy

import os
from typing import List, Optional
from generate import generate_mp4
from generate_photo_dump import generate_photo_dump_mp4
from database.crud import create_scene_db, create_voiceover_db, get_projects_db, get_project_db, remove_project_db, update_voiceover_db, update_scene_db, update_pd_project_db, create_project_db, copy_project_db

from script.generate_script import ScriptGenerator

import re
from websocket import WebSocketTaskManager

router = APIRouter(prefix="/projects", tags=["projects"])

def get_save_name(name):
        name = re.sub(r'[\\/:*?"<>|]', '', name)
        # optionally replace spaces with underscores
        name = name.replace(" ", "_")
        return name

@router.get("")
async def get_projects():
    projects = await get_projects_db()
    return projects

@router.get("/{project_id}")
async def get_project(
        project_id: str, 
    ):
    return await get_project_db(id=project_id)

class ScriptIn(BaseModel):
    topic: str
    duration: int
    description: Optional[str]
    data: Optional[str]
    gather_data: bool
    persistant_characters: bool
    reference_stories: Optional[str]

@router.post("/generate-script")
async def script_generation(request: ScriptIn):
    # word_count = estimated word count approximating to 180 words per minute.
    word_count = request.duration * 180 / 60

    STORY_SAMPLES_COUNT = 3

    try:
        story_data = None
        if request.data:
            story_data = request.data
        elif request.gather_data:
            pass
            # story_data = gather_story_data(request.title)

        llm_client = LLM(
            provider="xai",
            ai_model="grok-4-1-fast-reasoning",
        )

        scripts = []

        task = WebSocketTaskManager(connection_type="global", message_type="script_generation")

        await task.send_json(
            message=f"🎬 Initializing script generation for {STORY_SAMPLES_COUNT} story samples...",
            status="init",
        )

        for i in range(STORY_SAMPLES_COUNT):

            await task.send_json(
                message=f"🖊️ Generating story sample {i+1} of {STORY_SAMPLES_COUNT}...",
                status="in_progress",
            )


            script_generator = ScriptGenerator(
                llm_client=llm_client,
                topic=request.topic,
                description=request.description,
                story_data=story_data,
                reference_stories=request.reference_stories,
                persistant_characters=request.persistant_characters,
                word_limit=word_count
            )

            script = await script_generator.generate()

            scripts.append(script)

        
        await task.send_json(
            message=f"🎉 Finished generating story sample {STORY_SAMPLES_COUNT} of {STORY_SAMPLES_COUNT}.",
            status="finished"
        )

        return {
            "scripts": scripts
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ProjectIn(BaseModel):
    topic: str
    script: str

@router.post("/create-project")
async def create_project(
    project_in: ProjectIn,
):
    script = project_in.script
    topic = project_in.topic

    task = WebSocketTaskManager(connection_type="global", message_type="create_project")

    await task.send_json(
        message=f"🎬 Initializing project creation for topic: {topic}...",
        status="init"
    )
    

    await task.send_json(
        message=f"✂️ Splitting script...",
        status="in_progress"
    )


    splitted_script = split_script(script)

    await task.send_json(
        message=f"🖼️ Adding scenes..",
        status="in_progress"
    )

    script_with_scenes = await generate_scenes(
        llm_client=LLM(provider="xai", ai_model="grok-4-1-fast-reasoning"),
        splitted_script=splitted_script,
    )

    # prepare data for project creation

    await task.send_json(
        message=f"💾 Creating project in database...",
        status="in_progress"
    )

    project_id = str(uuid.uuid4())
    await create_project_db(id=project_id, name=topic, type="BASIC")
    
    await task.send_json(
        message=f"🔊 Saving voiceovers and scenes...",
        status="in_progress"
    )

    for script_part in script_with_scenes:

        start_time = float(script_part.get("start_time", 0.0))

        await create_voiceover_db(
            project_id=project_id,
            text=script_part["text"],
            start_time=start_time,
            duration=script_part.get("duration", 0.0)
        )

        
        for i, scene in enumerate(script_part["scenes"]):
            await create_scene_db(
                project_id=project_id,
                start_time=start_time + (i * 3.0),
                video_prompt=scene["video_prompt"],
                duration= 3.0,
                images=[
                    {
                        "prompt": scene["image_prompt"],
                        "time": "start"
                    }
                ]
            )

    await task.send_json(
        message=f"🎉 Project created successfully!",
        status="finished"
    )

    return {
        "message": "Project created successfully",
        "project_id": project_id
    }




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
