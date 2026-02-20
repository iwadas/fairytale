from fastapi import APIRouter, HTTPException, Body, UploadFile, File, Form, BackgroundTasks

from typing import Optional, List
import os
from AI.diffusion import Diffusion
import uuid
from database.crud import get_scene_db, update_scene_db, create_scene_db, remove_scene_db, remove_scene_image_db, create_or_update_scene_image_db

from pydantic import BaseModel
from services.save_file import save_file

from websocket import socket_manager

router = APIRouter(prefix="/scenes", tags=["scenes"])


class TypingSceneRequest(BaseModel):
    text: str

@router.post("/{project_id}")
async def create_scene(
    project_id: str,
    start_time: Optional[float] = Body(0.0, embed=True),                       
):
    new_scene = await create_scene_db(
        project_id=project_id,
        duration=3.0,
        start_time=start_time,
    )

    return {
        "message": "Scene created successfully",
        "scene": new_scene
    }
    

@router.delete("/{scene_id}")
async def delete_scene(scene_id: str):
    await remove_scene_db(scene_id)
    return {"message": "Scene deleted successfully"}

@router.post("/generate-image/{scene_id}")
async def generate_scene_image(
    scene_id: str,
    files: Optional[List[UploadFile]] = File(None),  # Catch ALL files
    lowkey: bool = Form(False),
    prompt: str = Form(...),
    scene_image_id: Optional[str] = Form(None),
    time: Optional[str] = Form(None),
):
    # TODO
    pass

@router.put("/upload-video/{scene_id}")
async def upload_scene_video(
    scene_id: str,
    video: UploadFile = File(...),
):
    scene = await get_scene_db(scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    
    video_src = await save_file(video, type="scene_video")

    await update_scene_db(scene_id, video_src=video_src)
    return {"message": "Scene video uploaded successfully", "scene_id": scene_id, "video_url": video_src}


@router.delete("/remove-image/{scene_image_id}")
async def remove_scene_image(
    scene_image_id: str,
):
    await remove_scene_image_db(scene_image_id)
    return {"message": "Scene image removed successfully", "scene_image_id": scene_image_id}

@router.put("/upload-image/{scene_id}")
async def upload_scene_image(
    scene_id: str,
    time: str = Body(..., embed=True),
    scene_image_id: Optional[str] = Body(None, embed=True),
    scene_image_prompt: Optional[str] = Body(None, embed=True),
    image: UploadFile = File(...),
):
    scene = await get_scene_db(scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    
    src = await save_file(image, type="scene_image")

    updated_scene_image = await create_or_update_scene_image_db(
        id=scene_image_id,
        scene_id=scene_id,
        src=src,
        prompt=scene_image_prompt,
        time=time,
    )

    return {"message": "Scene image uploaded successfully", "scene_image": updated_scene_image}

async def process_video_task(scene_id: str, prompt: str, duration: float, frames: list):
    """
    This function runs in the background. 
    It handles the slow diffusion process and DB updates.
    """
    try:

        task_id = str(uuid.uuid4())
        await socket_manager.broadcast_json(message={"status": "init", "type": "scene_generation", "message": "🌐 Connecting to video generation provider...", "task_id": task_id})

        diffusion = Diffusion(
            provider="runware", 
            fps=24, 
            # 480p horizontal
            resolution=(1280, 720),
            steps=40, 
            diffusion_model="bytedance:seedance@1.5-pro"
        )

        await socket_manager.broadcast_json(message={"status": "in_progress", "type": "scene_generation", "message": "🎞️ Generating video...", "task_id": task_id})

        video_src = await diffusion.generate(
            prompt=prompt,
            frames=frames,
            duration=int(duration),
            filename=f"scene_{scene_id}"
        )

        await socket_manager.broadcast_json(message={"status": "in_progress", "type": "scene_generation", "message": "📁 Saving video...", "task_id": task_id})
        await update_scene_db(scene_id, video_src=video_src)

        await socket_manager.broadcast_json(message={"status": "finished", "type": "scene_generation", "message": "✅ Video saved successfully!", "task_id": task_id})
        await socket_manager.broadcast_json(type="scene_generation", scene_id=scene_id, message={"video_src": video_src})

    except Exception as e:
        print(f"Background task FAILED for scene {scene_id}: {e}")

@router.post("/generate-video/{scene_id}")
async def generate_scene_video(
    background_tasks: BackgroundTasks,
    scene_id: str,
    prompt: str = Body(..., embed=True),
    duration: int = Body(3, embed=True),
):
    print(scene_id)
    scene = await get_scene_db(scene_id)

    if not scene:
        raise HTTPException(404, "Scene not found")
    
    print("scene[images]", scene["images"])
    
    frames = [
        {"src": img["src"], "time": img["time"]}
        for img in scene["images"]
        if img["src"] is not None
    ]

    background_tasks.add_task(
        process_video_task, 
        scene_id, 
        prompt, 
        duration, 
        frames
    )

    return {
        "message": "Video generation started in background"
    }

# TODO
@router.post("/add-character-to-scene")
async def add_character_to_scene(
    scene_id: str = Body(..., embed=True),
    character_id: str = Body(..., embed=True),
):
  
    return
    # Fetch the scene with its characters relationship pre-loaded
    result = await session.execute(
        select(Scene).options(selectinload(Scene.characters)).filter_by(id=scene_id)
    )
    scene = result.scalars().first()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    # Fetch the character
    character = await session.get(Character, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    # Check if the character is already associated with the scene
    if character in scene.characters:
        raise HTTPException(status_code=400, detail="Character is already in the scene")

    # Add the character to the scene's characters relationship
    scene.characters.append(character)

    # Commit the transaction
    session.add(scene)
    await session.commit()
    await session.refresh(scene)

    return {"message": f"Character {character_id} added to scene {scene_id}"}