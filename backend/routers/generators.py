from fastapi import APIRouter, HTTPException, Body, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import func
import uuid

import json

import os

from db import Place, get_session, Project, Scene, Character, Voiceover

from .prompts import gather_story_data, generate_story, story_split, add_scenes_to_story, prepare_story_for_db, get_persistant_characters, add_character_changes

from schemas import PromptRequest, FixedPromptResponse
from pydantic import BaseModel
from typing import Optional, List

from openai import OpenAI
import instructor
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
open_ai_client = instructor.from_openai(OpenAI(api_key=OPENAI_API_KEY))

router = APIRouter(prefix="/generators", tags=["generators"])

@router.post('/fix-character-prompt')
async def fix_character_prompt(request: PromptRequest):
    print("Something")
    print("Original prompt:", request.prompt)

    response = open_ai_client.chat.completions.create(
        model="gpt-4o-mini",
        response_model=FixedPromptResponse,
        messages=[
            {"role": "system", "content": "You are a helpful assistant that improves character descriptions for AI image generation. Your output should be an JSON description of scene that will be used for AI image generation"},
            {"role": "user", "content": request.prompt}
        ]
    )
    fixed_prompt = response.fixed_prompt  # Access directly (Instructor parses it for you)
    print("Fixed prompt:", fixed_prompt)
    return {"fixed_prompt": fixed_prompt}


class FixImagePrompt(BaseModel):
    prompt: str
    style: Optional[str]
    style_power: int


styles = {
    "lifelaps": (
        "hyper-realistic. "
        "Set in a dark, intimate night environment with deep shadows and low ambient light. "
        "Extreme photorealism with razor-sharp details on the main subject, cinematic shallow depth of field "
        "creating creamy bokeh in the blurred background. Dramatic low-key lighting: a strong, focused key light "
        "sculpting the face and body with rich contrast, subtle cool rim light separating the subject from the darkness, "
        "and faint warm accents for depth. Skin tones glow naturally under the light with visible texture and micro-details. "
        "Clean, modern aesthetic, perfect color grading with deep blacks, saturated highlights, "
        "and a moody teal-orange contrast for cinematic emotional impact. "
    ),
    "lifelaps_science": (
        "hyper-realistic. "
        "Set in a dark, futuristic lab at night with minimal ambient light and rich blackness. "
        "Extreme photorealism with razor-sharp details on the main subject, cinematic shallow depth of field "
        "creating creamy bokeh in the blurred background. Dramatic low-key lighting: a strong, focused key light "
        "sculpting the subject, subtle cool rim light, and faint warm fill for perfect skin tones and texture clarity. "
        "Subtle scientific holographic overlays float gently in the space around the subject: "
        "translucent glowing globes with soft descriptive labels, faint orbital paths, delicate molecular structures, "
        "and light data visualizations. These elements emit their own soft glow, enhancing the dark atmosphere "
        "without overpowering the subject. Deep volumetric light rays cut through the darkness, "
        "creating an immersive, high-tech aura. Clean, modern aesthetic, perfect color grading with deep blacks, "
        "neon accents, and a cool-warm contrast for emotional impact."
    ),
    "criminal": (
        "dark, cinematic noir with a mysterious and slightly unsettling aura — "
        "think high-stakes crime thriller, not horror. Use deep shadows, low-key lighting with a single dramatic light source "
        "(like a streetlamp, desk lamp, or moonlight cutting through blinds), desaturated colors dominated by cool blues, "
        "deep grays, and muted blacks with subtle accents of crimson or amber. Add atmospheric fog, light mist, or cigarette smoke "
        "drifting through beams of light. Sharp contrast, grainy film texture (35mm aesthetic), shallow depth of field "
        "to isolate the subject against a moody, blurred urban or industrial background. "
        "The mood is tense, secretive, and morally ambiguous — evoke suspicion, hidden motives, and quiet danger. "
        "Ultra-realistic skin textures, reflective wet surfaces, subtle lens flares, and micro-details in clothing and tools. "
        "No supernatural elements, no gore, no monsters — just raw human tension in a shadowy underworld."
    )
}

@router.post('/fix-scene-image-prompt')
async def fix_scene_image_prompt(request: FixImagePrompt):

    style = styles.get(request.style, False)    
    
    style_prompt = (
        f"Style description:\n"
        f"{style}\n\n"
        f"For the style: blend your expert creative judgment with the provided style description. "
        f"Apply it at intensity ({request.style_power}/10), where:\n"
        f"  • 1 = faint suggestion only\n"
        f"  • 5 = balanced, natural integration\n"
        f"  • 10 = dominant but still coherent\n\n"
        f"**CRITICAL RULE**: Never force any style element — no matter the intensity — if it damages realism, logic, or narrative coherence. "
        f"Lighting, color, mood, and composition are *always* non-negotiable foundations. "
        f"Any secondary effect (fog, grain, overlays, textures, etc.) must *earn its place*: "
        f"it is allowed **only if it actively strengthens the story, emotion, or visual impact** — "
        f"and **must be omitted** if it feels tacked-on, distracting, or out of context.\n\n"
        f"Your priority: a **professional, emotionally powerful, believable image** — "
        f"not a checklist. Style serves the scene. Never the reverse."
    )

    response = open_ai_client.chat.completions.create(
        model="gpt-4o-mini",
        response_model=FixedPromptResponse,
        temperature=0.7,
        messages=[
            {"role": "user", "content": (
                f"Scene description: {request.prompt}. "
                f"Correct this prompt to be suitable for AI image generation in JSON detailed description format. "
                f"{style_prompt if style else ''}"
            )}
        ]
    )
    fixed_prompt = response.fixed_prompt  # Access directly (Instructor parses it for you)
    print("Fixed prompt:", fixed_prompt)
    return {"fixed_prompt": fixed_prompt}


class FixVideoPrompt(BaseModel):
    image_prompt: str
    video_prompt: str

@router.post('/fix-scene-video-prompt')
async def fix_scene_video_prompt(request: FixVideoPrompt):
    response = open_ai_client.chat.completions.create(
        model="gpt-4o-mini",
        response_model=FixedPromptResponse,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert prompt engineer for image-to-video AI generation. "   
                )
            },
            {
                "role": "user",
                "content": (
                    "Create the perfect short motion prompt.\n"
                    f"Reference image (you can see this perfectly — NEVER describe anything in it):\n{request.image_prompt}\n\n"
                    f"Rough video idea (turn this into smooth, natural motion ONLY — no new elements):\n{request.video_prompt}\n\n"
                    "Output ONLY the motion prompt, nothing else."
                    "PURE MOTION AND CHANGE ONLY — nothing else.\n\n"
                    "STRICT RULES (never break them):\n"
                    "1. NEVER describe anything static that is already visible in the reference image "
                    "(objects, people, animals, buildings, clothing, colors, lighting, materials, background, etc.).\n"
                    "2. NEVER add new objects, plants, water, flowers, animals, people, or any element not explicitly mentioned in the rough video idea.\n"
                    "3. NEVER make statues, paintings, or any inanimate objects move, breathe, walk, talk, or show emotion.\n"
                    "4. ONLY describe what actually moves or changes according to the user's rough video idea: "
                    "camera movement, wind, fabric, hair, particles, light rays, shadows, dust, steam, fire, water (only if mentioned), etc.\n"
                    "5. DO NOT use any camera terms (zoom, pan, dolly, tilt, etc.) — describe the visual effect of movement instead.\n"
                    "6. DO NOT mention timing, keyframes, duration, or any technical terms.\n"
                    "7. Use vivid, poetic, sensory language.\n"
                    "8. Make everything feel like one single, continuous, living moment.\n\n"

                    "If the rough video idea asks for zero motion or is impossible with these rules, "
                    "write a prompt that describes only the tiniest natural atmospheric shifts (dust floating, faint heat haze, etc.)."
                )
            }
        ]
    )
    fixed_prompt = response.fixed_prompt  # Access directly (Instructor parses it for you)
    print("Fixed prompt:", fixed_prompt)
    return {"fixed_prompt": fixed_prompt}


class ProjectIn(BaseModel):
    title: str
    duration: int
    data: Optional[str]
    use_data: bool
    persistant_characters: bool
    reference_stories: Optional[str]

@router.post("/generate-script")
async def generate_script(request: ProjectIn, session: AsyncSession = Depends(get_session)):
    print("hello")
    print("Received project input:", request)
    
    
    # word_count = estimated word count approximating to 2 words per second.
    word_count = request.duration * 150 / 60

    try:
        if request.data:
            story_data = request.data
        elif request.use_data:
            story_data = gather_story_data(request.title).model_dump()
        else:
            story_data = None
            
        print("-----story data--------")
        print(json.dumps(story_data, indent=2))

        story = generate_story(request.title, word_count, story_data, request.reference_stories, request.persistant_characters).model_dump()["script"]

        splitted_story = story_split(story)
        print("-----story--------")
        print(json.dumps(splitted_story))

        story_with_scenes = add_scenes_to_story(splitted_story)
        print(json.dumps(story_with_scenes, indent=2))

        story_database_data = prepare_story_for_db(story_with_scenes, splitted_story)
        print("-----story for database--------")
        print(json.dumps(story_database_data, indent=2))

        if request.persistant_characters:
            scene_image_prompts = [scene["image_prompt"] for scene in story_database_data["scenes"]]
            character_changes = get_persistant_characters(scene_image_prompts, story_data)
            print("-----character changes-------")
            print(json.dumps(character_changes, indent=2))
            add_character_changes(story_database_data, character_changes)
    

        print("-----story with scenes and characters--------")
        print(json.dumps(story_database_data, indent=2))

        project = Project(
            id=str(uuid.uuid4()),
            name=request.title,
            created_at=func.now()
        )

        session.add(project)

        print("added project")
        if(request.persistant_characters):
            characters_map = {}
            for character in story_database_data["characters"]:
                character_db = Character(
                    id=str(uuid.uuid4()),
                    prompt = character["image_prompt"],
                    name = character["name"]
                )
                session.add(character_db)
                characters_map[character["name"]] = character_db
                project.characters.append(character_db)

        print("added characters")
        for scene in story_database_data["scenes"]:
            scene_db = Scene(
                id=str(uuid.uuid4()),
                duration=scene["duration"],
                start_time=scene["start_time"],
                image_prompt=scene["image_prompt"],
                video_prompt=scene["video_prompt"],
                project_id=project.id
            )
            session.add(scene_db)

            if "characters" in scene:
                for char_name in scene["characters"]:
                    if char_name in characters_map:
                        scene_db.characters.append(characters_map[char_name])


        print("added scenes")
        for voiceover in story_database_data["voiceovers"]:
            voiceover_db = Voiceover(
                id=str(uuid.uuid4()),
                text=voiceover["content"],
                text_with_pauses=voiceover["content_with_pauses"],
                project_id=project.id,
                start_time=voiceover["start_time"],  # Adjust based on scene timing if needed
                duration=voiceover["duration"],
                timestamps=None
            )
            session.add(voiceover_db)

        print("added voiceovers")


        await session.commit()

        return {"Success": True}


    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))