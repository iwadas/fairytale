import asyncio

from fastapi import APIRouter, HTTPException, Body, UploadFile, File, Form, BackgroundTasks

from moviepy import VideoFileClip
from typing import Optional, List
from AI.diffusion import Diffusion
from AI.llm import LLM
import uuid
from database.crud import get_scene_db, get_script_db, update_scene_db, create_scene_db, remove_scene_db, remove_scene_image_db, create_or_update_scene_image_db

from pydantic import BaseModel, Field
from services.save_file import save_file

from websocket import WebSocketTaskManager, socket_manager

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




@router.post("/{scene_id}/duplicate")
async def duplicate_scene(
    scene_id: str,
    
    start_time: Optional[float] = Body(0.0, embed=True),
    cut_start: Optional[float] = Body(0.0, embed=True),
    cut_end: Optional[float] = Body(0.0, embed=True),
    duration: Optional[float] = Body(0.0, embed=True),
    layer: Optional[int] = Body(2, embed=True),
    
):
    scene = await get_scene_db(scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    new_scene = await create_scene_db(
        project_id=scene["project_id"],
        video_src=scene["video_src"],
        duration=duration or scene["duration"],
        start_time=start_time or scene["start_time"] + scene["duration"],
        video_prompt=scene["video_prompt"],
        cut_start=cut_start or scene["cut_start"],
        cut_end=cut_end or scene["cut_end"],
        layer=layer or scene["layer"],
        images=scene["images"]
    )
    return new_scene


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

    return new_scene
    

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

def get_video_duration_sync(file_path: str) -> float:
    """Returns video duration in seconds using moviepy."""
    try:
        with VideoFileClip(file_path) as clip:
            return clip.duration
    except Exception as e:
        print(f"Error getting duration: {e}")
        return 0.0

@router.put("/upload-video/{scene_id}")
async def upload_scene_video(
    scene_id: str,
    video: UploadFile = File(...),
):
    scene = await get_scene_db(scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    
    video_src = await save_file(video, type="scene_video")
    
    duration = await asyncio.to_thread(get_video_duration_sync, video_src)

    await update_scene_db(scene_id, video_src=video_src, duration=duration)
    return {"message": "Scene video uploaded successfully", "scene_id": scene_id, "video_src": video_src, "duration": duration}


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
    
    src = await save_file(image, type="scene_image", remove_watermark_if_present=True)

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
    socket_notification_manager = WebSocketTaskManager(message_type="scene_video_generation", connection_type="global")
    socket_response_manager = WebSocketTaskManager(task_id=f"scene_video_generation_{scene_id}", message_type="scene_video_generation", connection_type="responses")
    try:
        await socket_notification_manager.send_notification(status="init", message="🌐 Connecting to video generation provider...")
        await socket_response_manager.send_response()
        # diffusion_client = await Diffusion.create()

        await socket_notification_manager.send_notification(status="in_progress", message="🎞️ Generating video...")

        # video_src = await diffusion_client.generate(
        #     prompt=prompt,
        #     frames=frames,
        #     duration=int(duration),
        #     filename=f"scene_{scene_id}"
        # )
        await asyncio.sleep(5)  # Simulate long-running process

        video_src = "static/videos/scenes\scene_f2a35ec5-009b-493d-818a-72f8808dd2df.mp4"


        await socket_notification_manager.send_notification(status="in_progress", message="📁 Saving video...")
        await update_scene_db(scene_id, video_src=video_src, duration=duration)

        await socket_notification_manager.send_notification(status="finished", message="✅ Video saved successfully!")
        
        
        print("SENDING TO NOT GLOBAL WEBSOCKET")
        await socket_response_manager.send_response(status="completed", data={"video_src": video_src}, source={"scene_id": scene_id})

    except Exception as e:
        await socket_notification_manager.send_notification(status="error", message=f"❌ Video generation failed. Error: {e}")
        await socket_response_manager.send_response()
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


class VideoPromptUpdate(BaseModel):
    new_video_prompt: str = Field(
        ..., 
        description="The updated video prompt following the exact [Camera Movement], [Subject Movement], [Speed/Vibe] format."
    )

@router.post("/fix-video-prompt/{scene_id}")
async def fix_video_prompt(
    background_tasks: BackgroundTasks,
    scene_id: str,
    new_camera_movement: str = Body(..., embed=True),
    additional_info: Optional[str] = Body(None, embed=True)
):
    scene = await get_scene_db(scene_id)
    if not scene or not scene.get("images"):
        raise HTTPException(404, "Scene or images not found")
    
    current_image_prompt = scene["images"][0].get("prompt", "")
    current_idea = scene["images"][0].get("idea", "")
    current_video_prompt = scene.get("video_prompt", "")

    info_instruction = f"User provided additional adjustments: {additional_info}" if additional_info else "No additional user adjustments provided."

    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert AI Prompt Engineer specializing in Image-to-Video diffusion models. "
                "Your task is to rewrite an existing video prompt to seamlessly integrate a NEW camera movement "
                "requested by the user, while maintaining generation stability and realistic physics."
            )
        },
        {
            "role": "user",
            "content": (
                "Here is the context of the scene:\n"
                f"- Base Idea: {current_idea}\n"
                f"- Reference Image Prompt (Already generated, DO NOT re-describe lighting/style): {current_image_prompt}\n"
                f"- Current Video Prompt: {current_video_prompt}\n\n"
                "--- TASK ---\n"
                f"1. Change the camera movement to: **{new_camera_movement}**\n"
                f"2. {info_instruction}\n\n"
                "--- RULES & CONSTRAINTS ---\n"
                "1. Format: You MUST strictly use the format: [Camera Movement], [Subject Movement], [Speed/Vibe].\n"
                "2. Motion Only: Do NOT describe lighting, style, colors, or static elements. The AI already has the reference image.\n"
                "3. Balance of Dynamics: The new camera movement and the subject's movement must work together without causing generation failure. If the subject performs macro-movements (like walking or interacting), apply stabilizing or smoothing modifiers to the camera movement. Avoid mixing highly chaotic camera action with fast subject action.\n"
                "4. Physical Realism: Subject movements must be anatomically and physically natural. Strictly avoid surrealism, morphing objects, or impossible physics.\n"
                "5. Secondary Motion: To enhance the dynamic feel without breaking the model's physics, utilize secondary motion in the environment or on the subject (e.g., wind effects, particles, clothing reacting to movement) rather than overcomplicating the subject's primary action.\n\n"
                "Generate ONLY the new prompt based on these rules."
            )
        }
    ]

    llm = await LLM.create()

    response = await llm.generate(
        messages=messages,
        response_format=VideoPromptUpdate
    )

    updated_scene = await update_scene_db(scene_id, video_prompt=response.new_video_prompt)
    
    return updated_scene




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