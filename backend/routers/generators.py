from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func
import uuid

import json

import os

from db import Place, get_session, Project, Scene, Character, Voiceover, SceneImage

from .prompts import gather_story_data, generate_story, story_split, add_scenes_to_story, prepare_story_for_db, get_persistant_characters, add_character_changes, estimate_speech_time

from schemas import PromptRequest, FixedPromptResponse
from pydantic import BaseModel
from typing import Optional, List
from openai import OpenAI
import instructor
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
XAI_API_KEY = os.getenv('XAI_API_KEY')

open_ai_client = instructor.from_openai(OpenAI(
    api_key=XAI_API_KEY,
    base_url="https://api.x.ai/v1",
))

router = APIRouter(prefix="/generators", tags=["generators"])


ai_model = "grok-4-1-fast-reasoning"



@router.post('/fix-character-prompt')
async def fix_character_prompt(request: PromptRequest):
    print("Something")
    print("Original prompt:", request.prompt)

    response = open_ai_client.chat.completions.create(
        model=ai_model,
        response_model=FixedPromptResponse,
        messages=[
            {"role": "system", "content": "You are a helpful assistant that improves character descriptions for AI image generation. Your output should be an JSON description of scene that will be used for AI image generation"},
            {"role": "user", "content": request.prompt}
        ]
    )
    fixed_prompt = response.fixed_prompt  # Access directly (Instructor parses it for you)
    print("Fixed prompt:", fixed_prompt)
    return {"fixed_prompt": fixed_prompt}


class FixVideoPrompt(BaseModel):
    full_voiceover_text: str
    selected_voiceover_text_part: str
    project_id: str

class SceneDescriptoinOption(BaseModel):
    image_description: str
    video_description: str

class NewSceneDescriptions(BaseModel):
    options: List[SceneDescriptoinOption]

@router.post('/generate-scene-image-prompts')
async def generate_scene_image_prompt(request: FixVideoPrompt, session: AsyncSession = Depends(get_session)):

    # # Fetch all the voiceovers for the project (id in request)
    # voiceovers = await session.execute(
    #     select(Voiceover).where(Voiceover.project_id == request.project_id)
    # )
    # voiceover_texts = [vo.text for vo in voiceovers.scalars().all()]
    # full_voiceover = " ".join(voiceover_texts)
    messages = [
            {
                "role": "system",
                "content": (
                    "You are a specialized Director of Photography AI. "
                    "Your goal is to generate a detailed scene description suitable for AI image generation based on a voiceover script. "
                    "Focus on visual elements like subject, environment, atmosphere, and composition."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Give me scene ideas  (visual representation for the words) for that should appear when those words are spoken: \"{request.selected_voiceover_text_part}.\"\n\n"
                    f"More context of the full sentence (Use when the spoken words don't give you enough information): {request.full_voiceover_text}\n\n"
                    "Output must be exactly 6 scene descriptions in the following format:\n"
                    "['option 1', 'option 2', 'option 3', 'option 4', 'option 5', 'option 6']\n\n"
                    
                    f"CRITICAL INSTRUCTION: You must strictly split the styles of the options (MAKE THEM SUITABLE FOR THE TARGET TEXT: \"{request.selected_voiceover_text_part}\"):\n"
                    " - OPTIONS 1-3: Cinematic Realism (Human scale, live-action style, dramatic, emotional).\n"
                    " - OPTIONS 4-6: Scientific/Abstract/Microscopic (Biology, Human parts (f.e brain/eye), neural networks, cellular level, or abstract data visualization).\n\n"

                    "All `image_description` descriptions must adhere to these pillars:\n"
                    "A. LIGHTING IS KEY: Never describe a scene without describing the light.\n"
                    "   - For Cinematic (1-3): Use 'rim-lit', 'volumetric fog', 'firelight glowing on skin', 'moonlight cutting through darkness'.\n"
                    "   - For Scientific (4-6): Use 'bioluminescent glow', 'subsurface scattering', 'neon electrical pulses against deep black void', 'translucent membrane lighting'.\n"
                    "B. ATMOSPHERE & TEXTURE: The air is never empty.\n"
                    "   - For Cinematic (1-3): Falling snow, rising dust, visible breath, rain on glass. Textures: fur, rust, grime, skin pores.\n"
                    "   - For Scientific (4-6): Floating organic particles, liquid suspension, electrical arcs, fibrous webs, glossy cellular surfaces.\n"
                    "C. SCALE & FRAMING: Avoid boring medium shots. Use either:\n"
                    "   - EPIC WIDE SHOTS: Massive environments or infinite abstract voids.\n"
                    "   - MACRO/MICROSCOPIC CLOSE-UPS: Focus on eyes/hands OR cellular structures/synapses with shallow depth of field (bokeh).\n\n"

                    "VIDEO DESCRIPTION SHOULD:\n"
                    "1. THE FORMULA: Start every prompt with a specific Camera Move + Subject Action.\n"
                    "2. ONE CAMERA MOVE: Use specific terms: 'Slow dolly push in', 'Microscopic camera pan', 'Drone flyover', 'Rack focus', 'Orbit', 'Camera flies to birds view', 'Hand held shaky camera'.\n"
                    "3. ONE SUBJECT MOVEMENT: Continuous loops: 'neurons firing rhythmically', 'DNA strand rotating', 'rain falling slowly', 'trembling hand'.\n"
                    "4. KINETIC ATMOSPHERE: Ensure the background is alive (e.g., 'particles drifting', 'electricity pulsing', 'fog rolling').\n"
                    "5. BE CONCISE: Focus on the vibe and the motion."
                )
            }
        ]

    print("prompt:")
    print(messages)
    print("---------")

    response = open_ai_client.chat.completions.create(
        model=ai_model,
        response_model=NewSceneDescriptions,
        messages=messages
    )
    print("Generated scene image prompt:", response)
    return {"new_scene_descriptions": response}


class FixImagePrompt(BaseModel):
    prompt: str
    style: Optional[str]
    style_power: int


styles = {
    "lifelaps": (
        "A cinematic still, presented in a wide aspect ratio with a dark, moody, and highly atmospheric aesthetic. "
        "The lighting is low-key and high-contrast, characterized by deep, crushing shadows and strong, "
        "directional key lighting (such as rim light, side light, or motivated natural light like fire or moonlight) that sculpts the subjects. "
        "The color palette is desaturated and muted, often with a dominant cool (blue, grey) or warm (golden, orange) tonal grade, creating a serious, epic, or contemplative tone."
        "The image should be hyper-realistic with immense detail on the focal point, "
        "a shallow depth of field creating significant bokeh in the background, and a subtle film grain texture throughout. "
        "The subjects, whether people, animals, or environments, are rendered with a sense of gravity and drama."
        "Try to add amazing angle that adds depth and interest to the composition."
        "Use particles in the air, volumetric light rays, and atmospheric effects to enhance the mood. "
    ),
    "lifelaps_mine": (
        "hyper-realistic. "
        "Set in a dark, intimate night environment with deep shadows and low orange ambient light. "
        "Extreme photorealism with razor-sharp details on the main subject, cinematic shallow depth of field "
        "creating creamy bokeh in the blurred background. Dramatic low-key lighting: a strong, focused key light "
        "sculpting the face and body with rich contrast, subtle warm orange rim light separating the subject from the darkness, "
        "and faint golden orange accents for depth. Skin tones glow naturally under the light with visible texture and micro-details. "
        "Clean, modern aesthetic, perfect color grading with deep blacks, saturated orange highlights, "
        "and warm golden contrast for cinematic emotional impact."

    ),
    "lifelaps_science": (
        "A cinematic still, presented in a wide aspect ratio with a dark, moody, and highly atmospheric aesthetic. "
        "The lighting is low-key and high-contrast, characterized by deep, crushing shadows and strong, "
        "directional key lighting (such as rim light, side light, or motivated natural light like fire or moonlight) that sculpts the subjects. "
        "The color palette is desaturated and muted, often with a dominant cool (blue, grey) or warm (golden, orange) tonal grade, creating a serious, epic, or contemplative tone."
        "The image should be hyper-realistic with immense detail on the focal point, "
        "a shallow depth of field creating significant bokeh in the background, and a subtle film grain texture throughout. "
        "The subjects, whether people, animals, or environments, are rendered with a sense of gravity and drama."
        "(OPTIONAL) Subtle scientific holographic overlays float gently in the space around the subject: "
        "translucent descriptive labels, faint orbital paths, delicate molecular structures, "
        "and light data visualizations. These elements emit their own soft glow, enhancing the dark atmosphere "
        "without overpowering the subject. Deep volumetric light rays cut through the darkness, "
        "creating an immersive, high-tech aura. Clean, modern aesthetic, perfect color grading with deep blacks, "
        "Try to add amazing angle that adds depth and interest to the composition."
        "Use particles in the air, volumetric light rays, and atmospheric effects to enhance the mood. "
    ),
    "lifelaps_science_mine": (
        "hyper-realistic. "
        "Set in a dark, at night with minimal ambient orange light and rich blackness. "
        "Extreme photorealism with razor-sharp details on the main subject, cinematic shallow depth of field "
        "creating creamy bokeh in the blurred background. Dramatic low-key lighting: a strong, focused key light "
        "sculpting the subject, subtle cool warm orange rim light, and faint warm orange fill for perfect skin tones and texture clarity. "
        "(OPTIONAL) Subtle scientific holographic overlays float gently in the space around the subject: "
        "translucent descriptive labels, faint orbital paths, delicate molecular structures, "
        "and light data visualizations. These elements emit their own soft glow, enhancing the dark atmosphere "
        "without overpowering the subject. Deep volumetric light rays cut through the darkness, "
        "creating an immersive, high-tech aura. Clean, modern aesthetic, perfect color grading with deep blacks, "
        "orange neon accents, and a warm contrast for emotional impact."
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
        f"Try to adjust my current image description to be enchanced by fitting elements from description. Make sure the style elements fit naturally into the scene and do not overpower it.\n\n"
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
        f"9:16 aspect ratio."
    )

    response = open_ai_client.chat.completions.create(
        model=ai_model,
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
    image_prompt: Optional[str]
    video_prompt: str

@router.post('/fix-scene-video-prompt')
async def fix_scene_video_prompt(request: FixVideoPrompt):
    response = open_ai_client.chat.completions.create(
        model=ai_model,
        response_model=FixedPromptResponse,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a specialized Director of Photography AI. "
                    "Your goal is to translate a static scene description into a high-fidelity video generation prompt. "
                    "You prioritize physics, lighting changes, and cinematic camera moves."
                )
            },
            {
                "role": "user",
                "content": (
                    "### CONTEXT\n"
                    f"Static Scene Description: {request.image_prompt}\n"
                    f"User's Desired Motion: {request.video_prompt}\n\n"
                    
                    "### CRUTIAL RULES\n"
                    "1. I already have image generated so do not overexplain what is already on the image for a video.\n"

                    "### INSTRUCTIONS\n"
                    "1. ANALYZE: Identify the primary subject and the environment's physics (wind, gravity, light).\n"
                    "2. MOTION: Describe HOW the subject moves. Use words like 'rippling', 'swaying', 'striding', 'morphing', etc.\n"
                    "3. CAMERA: Select a specific cinematic move (Pan, Tilt, Dolly, Truck, Pedestal, Roll, etc.).\n"
                    "4. CONSTRAINT: Do not introduce new objects. The video must look exactly like the Reference Image, just moving.\n\n"
                    
                    "### FORMAT (Strictly follow this)\n"
                    "[Subject Motion describing weight and speed], [Specific Camera Move], [Lighting/Atmospheric interaction].\n\n"
                    
                    "### FALLBACK\n"
                    "If the user asks for 'no motion', output: 'Slow subtle parallax, dust motes dancing in light, extremely subtle atmospheric movement.'"
                )
            }
        ]
    )
    fixed_prompt = response.fixed_prompt  # Access directly (Instructor parses it for you)
    print("Fixed prompt:", fixed_prompt)
    return {"fixed_prompt": fixed_prompt}



class ProjectIn(BaseModel):
    title: str
    story: Optional[str]

@router.post("/create-project")
async def create_project(request: ProjectIn, session: AsyncSession = Depends(get_session)):
    try:
        splitted_story = story_split(request.story)
        print("-----story--------")
        print(json.dumps(splitted_story))

        story_with_scenes = add_scenes_to_story(splitted_story)
        print(json.dumps(story_with_scenes, indent=2))

        story_database_data = prepare_story_for_db(story_with_scenes, splitted_story)
        print("-----story for database--------")
        print(json.dumps(story_database_data, indent=2))

        print("-----story with scenes and characters--------")
        print(json.dumps(story_database_data, indent=2))

        project = Project(
            id=str(uuid.uuid4()),
            name=request.title,
            created_at=func.now(),
        )

        session.add(project)

        print("added project")
        # if(request.persistant_characters):
        #     characters_map = {}
        #     for character in story_database_data["characters"]:
        #         character_db = Character(
        #             id=str(uuid.uuid4()),
        #             prompt = character["image_prompt"],
        #             name = character["name"]
        #         )
        #         session.add(character_db)
        #         characters_map[character["name"]] = character_db
        #         project.characters.append(character_db)
        # print("added characters")

        for scene in story_database_data["scenes"]:
            scene_db = Scene(
                id=str(uuid.uuid4()),
                duration=scene["duration"],
                start_time=scene["start_time"],
                video_prompt=scene["video_prompt"],
                project_id=project.id
            )

            scene_image_db = SceneImage(
                id=str(uuid.uuid4()),
                prompt=scene["image_prompt"],
                scene_id=scene_db.id,
                time='start'
            )
            session.add(scene_image_db)
            session.add(scene_db)

            # if "characters" in scene:
            #     for char_name in scene["characters"]:
            #         if char_name in characters_map:
            #             scene_db.characters.append(characters_map[char_name])


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

        return {"success": True, "project_id": project.id}


    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    

class ScriptIn(BaseModel):
    title: str
    duration: int
    data: Optional[str]
    gather_data: bool
    persistant_characters: bool
    reference_stories: Optional[str]

@router.post("/generate-script")
async def generate_script(request: ScriptIn, session: AsyncSession = Depends(get_session)):
    # word_count = estimated word count approximating to 110 words per minute.
    word_count = request.duration * 80 / 60

    try:
        if request.data:
            story_data = request.data
        elif request.gather_data:
            story_data = gather_story_data(request.title).model_dump()
        else:
            story_data = None
            
        print("-----story data--------")
        print(json.dumps(story_data, indent=2))

        STORY_SAMPLES_COUNT = 2
        story_samples = []

        for i in range(STORY_SAMPLES_COUNT):
            story = generate_story(request.title, word_count, story_data, request.reference_stories, request.persistant_characters).model_dump()["script"]
            story_samples.append({
                "story": story,
                "estimated_time": estimate_speech_time(story)
            })
            print(f"-----story sample {i+1}--------")

        return {"story_samples": story_samples}

    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))