from fastapi import APIRouter, HTTPException, Body, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import func
import uuid

import os

from db import Place, get_session, Project, Scene, Character, Voiceover


from schemas import PromptRequest, FixedPromptResponse
from pydantic import BaseModel
from typing import Optional, List

from openai import OpenAI
import instructor
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
open_ai_client = instructor.from_openai(OpenAI(api_key=OPENAI_API_KEY))

router = APIRouter(tags=["generators"])

@router.post('/fix-character-prompt')
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

@router.post('/fix-scene-image-prompt')
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

class PlaceOut(BaseModel):
    id: str
    name: str
    prompt: str

class SceneOut(BaseModel):
    scene_number: int
    duration: int
    image_prompt: str
    video_prompt: str
    character_ids: List[str]
    places_ids: List[str]

class VoiceoverOut(BaseModel):
    id: str
    text: str
    start_time: int

class ProjectOut(BaseModel):
    characters: List[CharacterOut]
    scenes: List[SceneOut]
    voiceovers: List[VoiceoverOut]
    places: List[PlaceOut]


@router.post("/generate-script")
async def generate_script(request: ProjectIn, session: AsyncSession = Depends(get_session)):
    print("hello")
    print("Received project input:", request)
    try:
        messages = [
            {
                "role": "system",
                "content": """
                    You are a professional cinematic scriptwriter who creates short documentary-style film scripts.
                    You write for AI-generated films, ensuring that every element (voiceover, visuals, characters, and places)
                    is coherent, historically immersive, and paced like a real short documentary.
                """
            },
            {
                "role": "user",
                "content": f"""
                    Generate a short cinematic documentary script for the project below.

                    Project title: {request.title}
                    Style: {request.style}
                    Voice style: {request.voiceover_style}
                    Prompt (story/idea): {request.prompt}
                    Total duration: {request.duration} seconds

                    --- 🎯 GOAL ---
                    Create a film script that tells a historical or true-crime story in a **cinematic, emotionally powerful way**.
                    The **voiceover** should drive the story — explaining key events, emotions, and context — while scenes
                    provide **visual storytelling support** through varied styles like reenactments, archival shots, and documents.

                    --- 🎬 STRUCTURE (JSON output must include) ---
                    1. **characters**: a list of recurring people used in the story.
                        Each character must include:
                        - "id": UUID
                        - "name"
                        - "role": e.g., "killer", "witness", "detective", "tourist", etc.
                        - "description": brief backstory or relevance to the story
                        - "appearance_prompt": detailed JSON-like description (for AI image generation) — include clothing, facial expression, lighting mood, etc.

                    2. **places**: a list of recurring locations.
                        Each place must include:
                        - "id": UUID
                        - "name"
                        - "description": why it matters to the story
                        - "appearance_prompt": JSON-like description (architecture, environment, weather, time period)

                    3. **scenes**: a list of short cinematic moments (1–5 seconds each).
                        Each scene must include:
                        - "id": UUID
                        - "order": sequential number
                        - "duration": float (in seconds)
                        - "place_id": optional (reference to a valid place)
                        - "character_ids": list of up to 3 valid character IDs appearing in the scene
                        - "scene_type": one of ["3d_animation", "historical_evidence", "information_on_screen"]
                        - "description": cinematic summary of what happens or is shown
                        - "image_prompt": JSON-like description of visual composition, colors, atmosphere, lighting, camera perspective
                        - "video_prompt": how the camera moves (slow pan, dolly, handheld, static archival feel, etc.)
                        - "text_on_screen" (optional): for timestamps, quotes, or contextual notes

                        🧩 Notes on scene types:
                        - **3d_animation** → dynamic reenactments or environmental shots (villages, people, movement)
                        - **historical_evidence** → documents, police reports, photos, newspapers, mugshots, etc.
                        - **information_on_screen** → contextual inserts, dates, quotes, witness lines (e.g. “Witness: I saw a stranger that night”)

                    4. **voiceovers**: multiple narration segments aligned to the timeline.
                        Each voiceover must include:
                        - "id": UUID
                        - "start_time": float
                        - "end_time": float
                        - "text": narration content (documentary narrator, not a character)
                        - "related_scene_ids": list of one or more scene IDs being narrated

                    --- 🎙️ VOICEOVER RULES (IMPORTANT) ---

                    - The narrator speaks for **most of the film (around 70–90% of total runtime)**.
                    - Only allow **short pauses (1–3 seconds)** for visual or emotional silence — e.g., showing a newspaper headline, or a slow zoom on a murder scene.
                    - The narration should *continuously tell the story* in a cinematic, documentary way.

                    - Think of pacing like:
                    "The camera shows [X]. The narrator describes what is happening — what the viewer sees — and gives emotional or factual context."

                    - Example of timing:
                    If total duration = 60s:
                        - Voiceover total time ≈ 45–55 seconds
                        - Pauses total time ≈ 5–15 seconds (distributed naturally)
                    
                    - Each voiceover segment should:
                    1. Correspond directly to the visuals of the connected scene(s)
                    2. Advance the story — describe what happened, who, when, where, or what emotion is present
                    3. Maintain a serious, investigative tone

                    - Example style:
                        VOICEOVER (matching visuals):
                        "Zakopane, 1975. A quiet winter town... until one night, the silence was shattered."
                        (pause, scene of blood in snow)
                        "The police found a young couple, their cabin door broken down. No witnesses. Only footprints — leading into the woods."

                    - The voiceover should make the viewer **understand and feel** the unfolding story — not just give facts occasionally.
                    - The narrator is omniscient but cinematic: sometimes factual, sometimes emotional, always forward-moving.

                    - Avoid long gaps (over 5 seconds) without narration unless they are dramatically necessary.

                    - Every few scenes should have a directly corresponding voiceover segment that describes exactly what’s being shown.
                    - If a scene has no voiceover, it must represent a purposeful pause — e.g., visual breathing moment, silent evidence reveal, or dramatic transition.

                    - Make sure it is synced with the scenes - if a scene shows a newspaper headline, the voiceover should briefly mention it.
                    - The total duration of all voiceover segments combined should be approximately 70-90% of the total film duration.

                    --- 👥 CHARACTERS & PLACES RULES ---
                    - If a person or location appears in multiple scenes, define them once and reuse via ID reference.
                    - Use consistent roles (killer, witness, police, tourist, narrator focus).
                    - Avoid re-describing the same visual details for the same entities across scenes.

                    --- 🎨 SCENE COMPOSITION GUIDELINES ---
                    - Use varied **scene_type** values to achieve a realistic, cinematic pacing:
                        * Example sequence:
                            1. 3d_animation → establishing view of Zakopane
                            2. historical_evidence → police report close-up
                            3. information_on_screen → “Zakopane, 1970s”
                            4. 3d_animation → killer moving through snow
                            5. historical_evidence → newspaper headline
                            6. 3d_animation → arrest scene
                            7. information_on_screen → “Suspect executed in 1978”
                            8. 3d_animation → final emotional ending
                    - Mix styles for visual rhythm — don’t make all scenes animated.
                    - Each transition should feel cinematic, not abrupt.

                    --- ⚙️ TECHNICAL REQUIREMENTS ---
                    - Generate valid UUIDs for all entities.
                    - Ensure all scene and voiceover references are valid and consistent.
                    - Voiceovers must reference real scene IDs.
                    - The total duration of scenes ≈ {request.duration} seconds.
                    - All output must be in English.
                    - Keep historical accuracy tone even if dramatized.

                    --- ✅ OBJECTIVE ---
                    Produce a film script that feels like a *cinematic short documentary* — combining narration, historical materials,
                    and cinematic visuals to tell the story clearly, emotionally, and chronologically.
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

        # Save Places
        place_map = {}  # To map place names to DB objects
        for place_out in project_out.places:
            if place_out.name not in place_map:
                place = Place(
                    id=str(uuid.uuid4()),
                    name=place_out.name,
                    prompt=place_out.prompt,
                    src=""  # Placeholder, to be generated later
                )
                session.add(place)
                place_map[place_out.id] = place
                # Associate place with project
                project.places.append(place)


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
            for place_id in scene_out.places_ids:
                if place_id in place_map:
                    scene.places.append(place_map[place_id])

        # Save Voiceovers
        for vo_out in project_out.voiceovers:
            voiceover = Voiceover(
                id=vo_out.id,
                text=vo_out.text,
                project_id=project.id,
                start_time=vo_out.start_time,  # Adjust based on scene timing if needed
            )
            session.add(voiceover)

        # Commit all changes
        await session.commit()

        # RETURN PROJECT OUTPUT ID
        return {"project_id": project.id}

    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))