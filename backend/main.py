from unittest import result
from xmlrpc import client
import time
import mimetypes  # Add this import at the top of your file
from sqlalchemy.orm import Session
from fastapi import FastAPI, HTTPException, Body, UploadFile, File, Form, Depends
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
import time
from datetime import datetime
import uuid
import json
import os
import requests
from pathlib import Path
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.cors import CORSMiddleware as StarletteCORSMiddleware
from typing import List
from PIL import Image
import base64
from io import BytesIO

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import func

from fastapi import Depends
from db import async_session_maker, Project, Scene, Character, Voiceover

# Google GenAI
from google import genai  
from google.genai import types

# ElevenLabs
from elevenlabs import ElevenLabs, save

# OpenAI
from openai import OpenAI
import instructor

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GENAI_API_KEY = os.getenv("GENAI_API_KEY")
RUNWARE_API_KEY = os.getenv("RUNWARE_API_KEY")
ELEVEN_LABS_API_KEY = os.getenv("ELEVEN_LABS_API_KEY")
if not GENAI_API_KEY:
    raise RuntimeError("Ustaw GENAI_API_KEY w środowisku (np. w .env)")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in .env")
if not RUNWARE_API_KEY:
    raise ValueError("RUNWARE_API_KEY not found in .env")
if not ELEVEN_LABS_API_KEY:
    raise ValueError("ELEVEN_LABS_API_KEY not found in .env")

open_ai_client = instructor.from_openai(OpenAI(api_key=OPENAI_API_KEY))
google_client = genai.Client(api_key=GENAI_API_KEY)
eleven_labs_client = ElevenLabs(api_key=ELEVEN_LABS_API_KEY)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Your frontend origin
    allow_credentials=False,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

class NoCacheStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return response

app.mount("/static", NoCacheStaticFiles(directory="static"), name="static")

async def get_session() -> AsyncSession:
    async with async_session_maker() as session:
        yield session

# Define input model
class CharacterShortInput(BaseModel):
    name: str
    short_description: str

class ProjectOutput(BaseModel):
    id: str  # UUID as string
    name: str
    scenes: List["SceneOutput"]
    characters: List["CharacterOutput"]
    voiceovers: List["VoiceoverOutput"]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True  # For Pydantic 2.x

class ProjectBasicOutput(BaseModel):
    id: str
    name: str
    created_at: Optional[datetime]

    class Config:
        from_attributes = True

class VoiceoverOutput(BaseModel):
    id: str  # UUID as string
    src: Optional[str]
    text: Optional[str]
    project_id: str
    start_time: int
    duration: Optional[int]

    class Config:
        from_attributes = True

class CharacterOutput(BaseModel):
    id: str  # UUID as string
    name: str
    prompt: Optional[str]  # Description for AI image generation
    src: Optional[str]

    class Config:
        from_attributes = True

class SceneOutput(BaseModel):
    id: str  # UUID as string
    scene_number: int
    duration: Optional[int]  # <8 seconds
    image_prompt: Optional[str]  # Prompt for scene visuals, incorporating characters
    image_src: Optional[str]
    video_prompt: Optional[str]  # Prompt for scene video generation
    video_src: Optional[str]
    project_id: str
    characters: List[CharacterOutput]  # List of character IDs (UUID strings)

    class Config:
        from_attributes = True


def pil_to_part(path: str, mime="image/png") -> types.Part:
    with open(path, "rb") as f:
        data = f.read()
    return types.Part(
        inline_data=types.Blob(
            mime_type=mime,
            data=base64.b64encode(data).decode("utf-8"),
        )
    )


def file_to_part(file_obj, mime="image/png") -> types.Part:
    # Case 1: FastAPI UploadFile
    if hasattr(file_obj, "file"):
        data = file_obj.file.read()
    # Case 2: Regular file handle from open()
    elif hasattr(file_obj, "read"):
        data = file_obj.read()
    # Case 3: Just a path string
    elif isinstance(file_obj, (str, Path)):
        with open(file_obj, "rb") as f:
            data = f.read()
    else:
        raise TypeError(f"Unsupported file type: {type(file_obj)}")

    return types.Part(
        inline_data=types.Blob(
            mime_type=mime,
            data=base64.b64encode(data).decode("utf-8"),
        )
    )

def parse_skrypt(skrypt):
    scenes = []
    lines = skrypt.split('\n')
    current_scene = {}
    for line in lines:
        if line.strip().startswith('Scene'):
            if current_scene:
                scenes.append(current_scene)
            current_scene = {"start_img_desc": "", "end_img_desc": "", "voiceover": ""}
        elif 'Start img:' in line:
            current_scene['start_img_desc'] = line.split('Start img: ')[1] if 'Start img: ' in line else ""
        elif 'End img:' in line:
            current_scene['end_img_desc'] = line.split('End img: ')[1] if 'End img: ' in line else ""
        elif 'Voiceover:' in line:
            current_scene['voiceover'] = line.split('Voiceover: ')[1] if 'Voiceover: ' in line else ""
    if current_scene:
        scenes.append(current_scene)
    # Fallback: If parsing fails, create dummy scenes
    if not scenes:
        scenes = [{"start_img_desc": "Placeholder start", "end_img_desc": "Placeholder end", "voiceover": "Placeholder voiceover"}]
    return scenes



def generate_speech(text: str, filename="voiceover", directory="static/voiceovers/"):
    audio = eleven_labs_client.text_to_speech.convert(
        text=text,
        voice_id="21m00Tcm4TlvDq8ikWAM",  # example voice (Rachel)
        model_id="eleven_multilingual_v2"
    )

    # Make sure the directory exists
    os.makedirs(directory, exist_ok=True)

    # Build full file path
    output_path = os.path.join(directory, f"{filename}.mp3")

    # Write audio chunks to file
    with open(output_path, "wb") as f:
        for chunk in audio:
            f.write(chunk)

    return output_path


def generate_image(directory="static/images/default/", filename="image", prompt="Generate", content_images: dict = {}):
    contents = []
    for name, upload_file  in content_images.items():
        contents.append(f"This is {name}:")
        contents.append(file_to_part(upload_file))

    # Add final instruction
    contents.append(prompt)

    # SHOW contents for debugging
    print("Contents for image generation:")
    for content in contents:
        if isinstance(content, str):
            print("Text:", content)
        elif isinstance(content, types.Part):
            print("Part with mime type:", content.inline_data.mime_type)
        else:
            print("Unknown content type")

    response = google_client.models.generate_content(
        model="gemini-2.5-flash-image-preview",
        contents=contents,
    )

    for part in response.candidates[0].content.parts:
        if part.text is not None:
            print(part.text)
        elif part.inline_data is not None:
            image = Image.open(BytesIO(part.inline_data.data))
            output_dir = os.path.join(directory, f"{filename}.png")  # Safer path construction
            if os.path.exists(output_dir):
                try:
                    os.remove(output_dir)
                    print(f"Removed existing file: {output_dir}")
                except OSError as e:
                    print(f"Error removing existing file {output_dir}: {e}")
                    continue  # Skip saving if removal fails (optional)
            try:
                image.save(output_dir)
                print(f"Saved image to: {output_dir}")
            except Exception as e:
                print(f"Error saving image to {output_dir}: {e}")

    return f"{directory}/{filename}.png"


def generate_video(directory="static/videos/", filename="video", prompt="Generate", negative_prompt="", image_path=None, duration: int = 3):
    os.makedirs(directory, exist_ok=True)
    output_path = os.path.join(directory, f"{filename}.mp4")

    url = "https://api.runware.ai/v1/video/generate"
    headers = {
        "Authorization": f"Bearer {RUNWARE_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "taskType": "videoInference",
        "taskUUID": str(uuid.uuid4()),
        "model": "bytedance:1@1",
        "positivePrompt": prompt,
        "duration": duration,
        "outputType": "URL",       # ✅ only URL allowed
        "outputFormat": "mp4",
        "height": 480,
        "width": 864,
        "deliveryMethod": "async",
    }


    image_data_uri = None
    if image_path:
        if not os.path.exists(image_path):
            raise ValueError(f"Image path not found: {image_path}")
        
        with open(image_path, "rb") as f:
            img_bytes = f.read()
        
        # Detect MIME type
        mime_type, _ = mimetypes.guess_type(image_path)
        if mime_type is None:
            # Fallback to extension
            ext = os.path.splitext(image_path)[1].lower()
            if ext == '.png':
                mime_type = 'image/png'
        
        if not mime_type.startswith('image/') or mime_type.split('/')[-1] not in ['png', 'jpeg', 'webp']:
            raise ValueError(f"Unsupported image MIME type: {mime_type}")
        
        # Construct data URI with detected MIME type
        image_data_uri = f"data:{mime_type};base64,{base64.b64encode(img_bytes).decode('utf-8')}"
        print("Including image in payload")
        payload["frameImages"] = [{"inputImage": image_data_uri}]

    # Wrap in array as required by Runware
    request_body = [payload]

    response = requests.post(url, headers=headers, json=request_body, timeout=120)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Runware API error: {response.text}")

    result = response.json()
    print("Runware API response:", json.dumps(result, indent=2))
    if "errors" in result and result["errors"]:
        raise HTTPException(status_code=500, detail=f"Runware API errors: {result['errors']}")
    if "data" not in result or not result["data"]:
        raise HTTPException(status_code=500, detail=f"Unexpected Runware response: {result}")

    print("Polling started...")

 

    if "url" not in result["data"][0]:
        print("Task is pending, polling for result...")
        task_uuid = result["data"][0]["taskUUID"]
        print(f"Extracted task UUID: {task_uuid}")
        poll_url = "https://api.runware.ai/v1/task"  # Use base task endpoint
        max_attempts = 15
        poll_interval = 5

        poll_headers = {
            "Authorization": f"Bearer {RUNWARE_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # JSON payload for polling
        poll_payload = [{
            "taskUUID": task_uuid,
            "taskType": "getResponse",
        }]

        for attempt in range(max_attempts):
            time.sleep(poll_interval)
            try:
                print(f"Polling attempt {attempt + 1}/{max_attempts} for task UUID: {task_uuid}")
                poll_response = requests.post(poll_url, headers=poll_headers, json=poll_payload, timeout=30)
                poll_response.raise_for_status()
                poll_result = poll_response.json()
                print(f"Polling response: {json.dumps(poll_result, indent=2)}")

                if "data" in poll_result and poll_result["data"]:
                    if poll_result["data"][0].get("status") == "success":
                        video_url = poll_result["data"][0].get("videoURL")
                        if not video_url:
                            raise ValueError("Task completed but no video URL found")
                        print(f"Video URL retrieved: {video_url}")
                        break
                    elif poll_result["data"][0].get("taskStatus") == "FAILED":
                        raise HTTPException(status_code=500, detail=f"Video generation failed: {poll_result['data'][0].get('error', 'Unknown error')}")
            except requests.exceptions.HTTPError as e:
                print(f"Polling attempt {attempt + 1} failed with HTTP error: {e}")
                print(f"Response body: {poll_response.text}")
                if attempt == max_attempts - 1:
                    raise HTTPException(status_code=500, detail=f"Polling failed after {max_attempts} attempts: {e}")
            except requests.exceptions.RequestException as e:
                print(f"Polling attempt {attempt + 1} failed: {e}")
                if attempt == max_attempts - 1:
                    raise HTTPException(status_code=500, detail=f"Polling failed after {max_attempts} attempts: {e}")
        else:
            raise HTTPException(status_code=500, detail=f"Video generation timed out after {max_attempts * poll_interval} seconds")
    else:
        video_url = result["data"][0]["videoURL"]

    # Download video from URL to local storage
    r = requests.get(video_url, stream=True, timeout=300)
    r.raise_for_status()
    with open(output_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    return output_path

def filename_from_name(name: str) -> str:
    return name.lower().replace(" ", "_")


# CHARACTERS ROUTES
@app.get("/images/characters/{character_id}")
async def get_character_image(character_id: str, session: AsyncSession = Depends(get_session)):
    character = await session.get(Character, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    if not character.src or not Path(character.src).exists():
        raise HTTPException(status_code=404, detail="Image file not found")
    return FileResponse(character.src, media_type="image/png")

@app.post("/characters")
async def create_character(
    name: str = Form(...),
    prompt: str = Form(...),
    image1: UploadFile = File(...),
    image2: Optional[UploadFile] = File(None),
    session: AsyncSession = Depends(get_session),
):
    # build content_images
    content_images = {"image1": image1}
    if image2:
        content_images["image2"] = image2

    image_path = generate_image(
        directory=f"static/images/characters",
        filename=filename_from_name(name),
        prompt=prompt,
        content_images=content_images
    )

    new_char = Character(id=str(uuid.uuid4()), name=name, prompt=prompt, src=image_path)
    session.add(new_char)
    await session.commit()
    await session.refresh(new_char)
    return {"message": "Character created successfully", "character_id": new_char.id, "image_path": image_path}


@app.put("/characters/{character_id}")
async def update_character(
    character_id: str,
    name: Optional[str] = Body(None),
    prompt: Optional[str] = Body(None),
    image1: Optional[UploadFile] = File(None),
    image2: Optional[UploadFile] = File(None),
    session: AsyncSession = Depends(get_session),
):
    character = await session.get(Character, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    if name is not None:
        character.name = name
    if prompt is not None:
        character.prompt = prompt

    if image1:
        content_images = {"image1": image1}
        if image2:
            content_images["image2"] = image2
        image_path = generate_image(
            directory=f"static/images/characters",
            filename=filename_from_name(name or character.name),
            prompt=prompt or character.prompt or "update",
            content_images=content_images
        )
        character.src = image_path

    session.add(character)
    await session.commit()
    await session.refresh(character)
    return {"message": f"Character {character_id} updated successfully", "character": CharacterOutput.model_validate(character).model_dump()}


@app.get("/characters")
async def list_characters(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Character))
    characters = result.scalars().all()
    # Return list of Pydantic objects or raw dicts
    return [CharacterOutput.model_validate(c).model_dump() for c in characters]


@app.delete("/characters/{character_id}")
async def delete_character(character_id: str, session: AsyncSession = Depends(get_session)):
    character = await session.get(Character, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    await session.delete(character)
    await session.commit()
    return {"message": f"Character {character_id} deleted"}


# PROJECTS ROUTES
@app.post("/projects")
async def create_project(name: str = Body(...), session: AsyncSession = Depends(get_session)):
    new_project = Project(id=str(uuid.uuid4()), name=name)
    session.add(new_project)
    await session.commit()
    await session.refresh(new_project)
    return {"project_id": new_project.id}


@app.delete("/projects/{project_id}")
async def delete_project(project_id: str, session: AsyncSession = Depends(get_session)):
    project = await session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await session.delete(project)
    await session.commit()
    return {"message": f"Project {project_id} deleted"}


@app.get("/projects")
async def list_projects(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Project))
    projects = result.scalars().all()
    return [ProjectBasicOutput.model_validate(p).model_dump() for p in projects]

@app.get('/projects/{project_id}')
async def get_project(project_id: str, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Project)
        .where(Project.id == project_id)
        .options(
            selectinload(Project.scenes)
                .selectinload(Scene.characters),
            selectinload(Project.characters),
            selectinload(Project.voiceovers),
        )
    )
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    # serialize with Pydantic
    return ProjectOutput.model_validate(project).model_dump()


class PromptRequest(BaseModel):
    prompt: str
class FixedPromptResponse(BaseModel):
    fixed_prompt: str

    # A fluffy Mega Knight, with a soft and fluffy exterior resembling a giant marshmallow. He has large, expressive eyes and a playful smile, wearing a shiny, metallic armor that contrasts with his soft texture. The armor is detailed with swirling patterns and vibrant colors, and he holds a large sword made of candy. The background is a whimsical landscape, filled with colorful clouds and a bright blue sky.

@app.post('/fix-character-prompt')
async def fix_character_prompt(request: PromptRequest):
    print("Something")
    print("Original prompt:", request.prompt)

    response = open_ai_client.chat.completions.create(
        model="gpt-4o-mini",
        response_model=FixedPromptResponse,
        messages=[
            {"role": "system", "content": "You are a helpful assistant that improves character descriptions for AI image generation."},
            {"role": "user", "content": request.prompt}
        ]
    )
    fixed_prompt = response.fixed_prompt  # Access directly (Instructor parses it for you)
    print("Fixed prompt:", fixed_prompt)
    return {"fixed_prompt": fixed_prompt}

@app.post('/fix-scene-image-prompt')
async def fix_scene_image_prompt(request: PromptRequest):
    response = open_ai_client.chat.completions.create(
        model="gpt-4o-mini",
        response_model=FixedPromptResponse,
        messages=[
            {"role": "system", "content": "You are a helpful assistant that improves scene image prompts for AI image generation."},
            {"role": "user", "content": request.prompt}
        ]
    )
    fixed_prompt = response.fixed_prompt  # Access directly (Instructor parses it for you)
    print("Fixed prompt:", fixed_prompt)
    return {"fixed_prompt": fixed_prompt}


class ProjectIn(BaseModel):
    title: str  # Topic/story title
    style: str  # e.g., "epic fantasy", "noir thriller"
    voiceover_style: str  # e.g., "dramatic", "calm"
    prompt: str
    duration: int = 10  # Total film duration in seconds

class CharacterOut(BaseModel):
    id: str
    name: str
    prompt: str

class SceneOut(BaseModel):
    scene_number: int
    duration: int
    image_prompt: str
    video_prompt: str
    character_ids: List[str]

class VoiceoverOut(BaseModel):
    id: str
    text: str
    start_time: int
    duration: int

class ProjectOut(BaseModel):
    characters: List[CharacterOut]
    scenes: List[SceneOut]
    voiceovers: List[VoiceoverOut]

@app.post("/generate-script")
async def generate_script(request: ProjectIn, session: AsyncSession = Depends(get_session)):
    print("hello")
    print("Received project input:", request)
    try:
        messages = [
            {
                "role": "system",
                "content": """
                    You are a professional scriptwriter:
                """
            },
            {
                "role": "user",
                "content": f"""
                    Generate a cinematic and entertaining short video script for the project below.

                    Project title: {request.title}
                    Style: {request.style}
                    Voice style: {request.voiceover_style}
                    Prompt (story/idea): {request.prompt}
                    Total duration: {request.duration} seconds

                    Rules:
                    - Scenes must be very quick (1-5 seconds) and visually dynamic.
                    - Each scene should be cinematic and engaging, with a strong sense of pacing.
                    - The sum of all scene durations should be close to {request.duration} seconds.
                    - Scene Attribute "image_prompt" must describe the scene's visual elements, including characters and setting. I would already include how Characters looks so you do not need to additionaly describe them.
                    - Scene Attribute "video_prompt" will be used for generating video based in image generated of the scene - so it must describe the desired camera angles, movements, and any other visual effects.
                    - Voiceover must be delivered by a lector, not a character from the scenes, narrating the current actions or events in the scenes in a {request.voiceover_style} tone.
                    - Voiceover start times and durations must be independent of scene durations. Each voiceover should start at a specific time that aligns with the actions or events it describes, which may be in the middle of a scene, span multiple scenes, or include pauses with no voiceover in some scenes.
                    - Voiceover start times must vary and not default to 0. Assign start times based on when the described action or event occurs in the timeline, ensuring logical alignment with the scene content.
                    - Voiceovers must not overlap; each voiceover's start time and duration must ensure that only one voiceover is active at any given time in the video timeline.
                    - Voiceover content must directly relate to the actions or events in the scenes it accompanies, enhancing the narrative without being dialogue from scene characters.
                    - Generate valid UUIDs for all IDs.
                    - Ensure character_ids in scenes reference valid character IDs from the characters list.
                """
            }
        ]

        # Call Open AI API
        project_out = open_ai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            response_model=ProjectOut  # Ensure JSON response
        )

        # Create new Project in database
        project = Project(
            id=str(uuid.uuid4()),
            name=request.title,
            created_at=func.now()
        )
        session.add(project)

        # Save Characters
        character_map = {}  # To map character IDs to DB objects
        for char_out in project_out.characters:
            character = Character(
                id=char_out.id,
                name=char_out.name,
                prompt=char_out.prompt
            )
            session.add(character)
            character_map[char_out.id] = character
            # Associate character with project
            project.characters.append(character)

        # Save Scenes and associate Characters
        for scene_out in project_out.scenes:
            scene = Scene(
                id=str(uuid.uuid4()),
                scene_number=scene_out.scene_number,
                duration=scene_out.duration,
                image_prompt=scene_out.image_prompt,
                video_prompt=scene_out.video_prompt,
                project_id=project.id
            )
            session.add(scene)
            # Associate characters with scene
            for char_id in scene_out.character_ids:
                if char_id in character_map:
                    scene.characters.append(character_map[char_id])

        # Save Voiceovers
        for vo_out in project_out.voiceovers:
            voiceover = Voiceover(
                id=vo_out.id,
                text=vo_out.text,
                project_id=project.id,
                start_time=vo_out.start_time,  # Adjust based on scene timing if needed
                duration=vo_out.duration  # Adjust if duration is calculable
            )
            session.add(voiceover)

        # Commit all changes
        await session.commit()

        # RETURN PROJECT OUTPUT ID
        return {"project_id": project.id}

    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-scene-image/{scene_id}")
async def generate_scene_image(
    scene_id: str,
    prompt: str = Body(..., embed=True),
    character_ids: Optional[List[str]] = Body(default=[]),
    image: Optional[UploadFile] = File(None),
    session: AsyncSession = Depends(get_session),
):
    # 1. Get character image paths from DB using ORM
    print("Character IDs for image generation:", character_ids)
    content_images = {}
    if character_ids:
        result = await session.execute(select(Character).where(Character.id.in_(character_ids)))
        characters = result.scalars().all()
        for char in characters:
            print(f"Looking for character image at: {char.name}")
            if char.src:
                image_path = Path(char.src)
                print(f"Looking for character image at: {image_path}")
                if image_path.exists():
                    print(f"✅ Found character image on disk: {char.src}")
                    content_images[char.name.lower().replace(" ", "_")] = open(image_path, "rb")
                else:
                    print(f"⚠️ Character image not found on disk: {char.src}")
            else:
                print(f"⚠️ Character {char.id} has no src")
    if image is not None:
        content_images["additional_image"] = image
        print("appended image")

    # 2. Generate filename for scene
    filename = filename_from_name(f"scene_{scene_id}")

    # 3. Call your image generator
    print("Generating image with prompt:", prompt)
    image_path = generate_image(
        directory="static/images/scenes",
        filename=filename,
        prompt=prompt,
        content_images=content_images
    )

    # 4. Store or update scene image in DB (attach to scene)
    scene = await session.get(Scene, scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    scene.image_src = image_path
    scene.image_prompt = prompt
    session.add(scene)

    await session.commit()
    # optionally refresh scene/image
    await session.refresh(scene)
    return {"message": "Scene image generated successfully", "scene_id": scene_id, "image_url": image_path}


@app.post("/upload-scene-image/{scene_id}")
async def upload_scene_image(
    scene_id: str,
    image: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
):
    # 1. Get scene from DB using ORM
    scene = await session.get(Scene, scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    # 2. Generate filename for scene
    filename = filename_from_name(f"scene_{scene_id}")

    # 3. Save uploaded image to disk
    output_dir = "static/images/scenes"
    os.makedirs(output_dir, exist_ok=True)
    image_path = os.path.join(output_dir, f"{filename}.png")  # Safer path construction
    try:
        with open(image_path, "wb") as f:
            f.write(image.file.read())
        print(f"Saved uploaded image to: {image_path}")
    except Exception as e:
        print(f"Error saving uploaded image to {image_path}: {e}")
        raise HTTPException(status_code=500, detail="Failed to save uploaded image")

    # 4. Store or update scene image in DB (attach to scene)
    scene.image_src = image_path
    session.add(scene)

    await session.commit()
    await session.refresh(scene)  # Refresh to confirm the update

    return {"message": "Scene image uploaded successfully", "scene_id": scene_id, "image_url": image_path}

@app.post("/generate-scene-video/{scene_id}")
async def generate_scene_video(
    scene_id: str,
    prompt: str = Body(..., embed=True),
    session: AsyncSession = Depends(get_session),
):

    # 1. Get scene image path from DB using ORM
    scene = await session.get(Scene, scene_id)
    print("Scene ID for video generation:", scene_id)
    if not scene:
        print("Scene not found")
        raise HTTPException(status_code=404, detail="Scene not found")
    if not scene.image_src or not Path(scene.image_src).exists():
        print("Scene image not found")
        raise HTTPException(status_code=400, detail="Scene image not found. Generate scene image first.")
    
    # 2. Generate filename for scene video
    filename = filename_from_name(f"scene_{scene_id}")

    # 3. Call the video generator
    print("Scene ID:", scene_id)
    print("Generating video with prompt:", prompt)
    print("Using scene image:", scene.image_src)
    print("Scene duration:", scene.duration)
    print("Generating video...")

    

    video_path = generate_video(
        directory="static/videos/scenes",
        filename=filename,
        prompt=prompt,
        negative_prompt="",  # Default to empty string, adjust if needed
        image_path=scene.image_src,
        duration=scene.duration  # Default duration, adjust as needed
    )

    # 4. Store or update scene video in DB (attach to scene)
    scene.video_src = video_path
    scene.video_prompt = prompt
    session.add(scene)

    await session.commit()

    # Optionally refresh scene/video
    await session.refresh(scene)

    return {"message": "Scene video generated successfully", "scene_id": scene_id}

@app.post("/generate-voiceover/{voiceover_id}")
async def generate_voiceover(voiceover_id: str, session: AsyncSession = Depends(get_session)):
    voiceover = await session.get(Voiceover, voiceover_id)

    if not voiceover:
        raise ValueError("Voiceover not found")
    if not voiceover.text:
        raise ValueError("Voiceover text is empty")

    filename = filename_from_name(f"voiceover_{voiceover_id}")
    audio_path = generate_speech(
        text=voiceover.text,
        filename=filename,
        directory="static/voiceovers"
    )

    voiceover.src = audio_path
    session.add(voiceover)
    await session.commit()
    await session.refresh(voiceover)
    return {"message": "Voiceover generated successfully", "voiceover_id": voiceover_id, "voiceover_src": audio_path}

@app.post("/add-character-to-scene")
async def add_character_to_scene(
    scene_id: str = Body(..., embed=True),
    character_id: str = Body(..., embed=True),
    session: AsyncSession = Depends(get_session),
):
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