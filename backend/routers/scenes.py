from fastapi import APIRouter, HTTPException, Body, UploadFile, File, Form, BackgroundTasks

from typing import Optional, List
from AI.diffusion import Diffusion
from AI.llm import LLM
import uuid
from database.crud import get_scene_db, get_script_db, update_scene_db, create_scene_db, remove_scene_db, remove_scene_image_db, create_or_update_scene_image_db

from pydantic import BaseModel, Field
from services.save_file import save_file

from websocket import socket_manager

router = APIRouter(prefix="/scenes", tags=["scenes"])


@router.post("/generate-image-prompts")
async def generate_scene_image_prompt(
    project_id: str = Body(..., embed=True),
    selected_voiceover_text_part: str = Body(..., embed=True),
    additional_info: Optional[str] = Body(None, embed=True)
):

    script = get_script_db(project_id)

    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert Director for Psychology and Philosophy video essays. "
                "Your ONLY job is to invent brilliant, striking visual metaphors for the provided script. "
                f"### FULL SCRIPT OVERVIEW:\n\"{script}\"\n\n"
                "Translate the script into raw visual concepts (Literal, Metaphorical, Abstract). "
                "Focus ONLY on the subjects, their actions, and the setting. Do NOT apply camera angles, lighting, or specific render styles. "
                "**NO TEXT ON SCREEN:** Never describe signs or words."
            )
        },
        {
            "role": "user",
            "content": (
                f"**Generate exactly 5 raw visual concepts for this sentence:**\n"
                f"\"{selected_voiceover_text_part}\"\n\n"
                "Make sure the concepts naturally progress from one to the next - but don't make it repetitive. Use different subjects, concepts, and settings for each scene.\n\n"
                f"{(f"Additional information about the generation (EXTREMELY IMPORTANT): {additional_info}\n\n") if additional_info else ""}"
            )
        }
    ]

    # Step 2: The Styled Scene & Motion
    class Scene(BaseModel):
        image_prompt: str = Field(
            description="The raw visual concept for the scene."
        )
        video_prompt: str = Field(
            description="Camera movement and action instructions based on the scene. Strict format: [Camera Movement], [Subject Movement], [Speed/Vibe]"
        )

    class ResponseScenes(BaseModel):
        scenes: List[Scene] = Field(
            description="A list of scene descriptions, each containing an image prompt and a video prompt."
        )

    llm = await LLM.create()
    response = await llm.generate(
        messages=messages,
        response_format=ResponseScenes
    )

    new_scene_descriptions = response.scenes

    print("Generated scene image prompt:", new_scene_descriptions)
    return {"new_scene_descriptions": new_scene_descriptions}



class NewPhotoDumpImages(BaseModel):
    options: List[str]


@router.post("/fix-image-prompt")
async def fix_image_prompt(
    scene_prompt: str = Body(..., embed=True),
    style: Optional[str] = Body(None, embed=True),
    style_power: Optional[float] = Body(0.5, embed=True),
):
    style = (
        "**VISUAL STYLE RULES (APPLY THESE TO THE RAW CONCEPT)**\n"
        "1. **Geometry:** Everything must be described as sharp, fractured, and splintered geometric forms.\n"
        "2. **Materials:** For every object, assign one of these: Polished Black Obsidian, Liquid Chrome/Mercury, Iridescent Oil Slick, Smoked Deep Crimson Glass, Vantablack, or Matte Bone White.\n"
        "3. **Environment:** Never leave the background empty. Describe a geometric/abstract version of the setting.\n\n"
        "Append this exactly to the end of the prompt: , hyper-realistic 3D render, fractured dark-aesthetic sculpture, flawless ultra-reflective surfaces, stark chiaroscuro studio lighting, piercing crimson and cold cyan rim lights, engulfing pitch-black shadows, macro photography depth of field, Octane render, raytracing, heavy caustics, psychological thriller mood, 8k"
    )


    system_message = {
        "role": "system",
        "content": (
            f"You are an expert art director specializing in a unique visual style defined by the following rules:\n"
            f"Your task is to enhance the provided scene description by naturally integrating elements of this style. "
            f"Remember: realism, logic, and narrative coherence are paramount. Style should enhance, not overpower."
        )
    }

    user_message = {
        "role": "user",
        "content": (
            f"Here is a visual description that was generated for a scene: {scene_prompt}\n\n"
            f"Try to adjust my current image description to be enchanced by fitting elements from description. Make sure the style elements fit naturally into the scene and do not overpower it.\n\n"
            f"Style description:\n"
            f"{style}\n\n"
            f"For the style: blend your expert creative judgment with the provided style description. "
            f"Apply it at intensity ({style_power}/10), where:\n"
            f"  • 1 = faint suggestion only\n"
            f"  • 5 = balanced, natural integration\n"
            f"  • 10 = dominant but still coherent\n\n"
            f"**CRITICAL RULE**: Never force any style element — no matter the intensity — if it damages realism, logic, or narrative coherence. "
            f"Lighting, color, mood, and composition are *always* non-negotiable foundations. "
            f"Your priority: a **professional, emotionally powerful, believable image** — "
            f"not a checklist. Style serves the scene. Never the reverse."
            f"1:1 aspect ratio."
        )
    }
    
    class FixedPromptResponse(BaseModel):
        prompt: str = Field(description="The fixed prompt, with applied style adjustments, ready for image generation.")

    llm = await LLM.create()
    response = await llm.generate(
        messages=[system_message, user_message],
        response_format=FixedPromptResponse
    )
    fixed_prompt = response.prompt  # Access directly (Instructor parses it for you)
    return {"fixed_prompt": fixed_prompt}




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