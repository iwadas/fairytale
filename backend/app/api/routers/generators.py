from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func
import uuid

import json
import logging

# from db import Place, get_session, Project, Scene, Character, Voiceover, SceneImage
from app.pipeline.story.legacy_prompts import gather_story_data, generate_story, story_split, add_scenes_to_story, prepare_story_for_db, get_persistant_characters, add_character_changes, estimate_speech_time

# from schemas import PromptRequest, FixedPromptResponse
from pydantic import BaseModel
from typing import Optional, List
from openai import OpenAI
import instructor

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_settings = get_settings()
XAI_API_KEY = _settings.xai_api_key.get_secret_value() if _settings.xai_api_key is not None else None

open_ai_client = instructor.from_openai(OpenAI(
    api_key=XAI_API_KEY,
    base_url=_settings.xai_base_url,
))

router = APIRouter(prefix="/generators", tags=["generators"])

ai_model = "grok-4-1-fast-reasoning"

# TODO
@router.post('/fix-character-prompt')
async def fix_character_prompt(request):
    return

    logger.debug("Original prompt: %s", request.prompt)

    response = open_ai_client.chat.completions.create(
        model=ai_model,
        response_model=FixedPromptResponse,
        messages=[
            {"role": "system", "content": "You are a helpful assistant that improves character descriptions for AI image generation. Your output should be an JSON description of scene that will be used for AI image generation"},
            {"role": "user", "content": request.prompt}
        ]
    )
    fixed_prompt = response.fixed_prompt  # Access directly (Instructor parses it for you)
    logger.debug("Fixed prompt: %s", fixed_prompt)
    return {"fixed_prompt": fixed_prompt}


class FixVideoPrompt(BaseModel):
    full_voiceover_text: str
    selected_voiceover_text_part: str
    project_id: str
    additional_info: Optional[str]

class SceneDescriptoinOption(BaseModel):
    image_description: str
    video_description: str

class NewSceneDescriptions(BaseModel):
    options: List[SceneDescriptoinOption]


class FixImagePrompt(BaseModel):
    prompt: str
    style: Optional[str]
    style_power: int


styles = {
    "darkwave_engraving": (
        "A dramatic 19th-century wood engraving or etching style illustration, reminiscent of Gustave Doré's 'Paradise Lost' "
        "or 'Divine Comedy' artwork. The visual style is defined by intricate cross-hatching, fine line work, "
        "and a high-contrast ink-on-paper texture. "
        "The entire image is washed in a deep, saturated monochromatic purple, violet, or indigo color grade, "
        "replacing traditional black and white with deep shadows and luminous purple highlights. "
        "The atmosphere is brooding, ethereal, and gothic, evoking a 'darkwave' or 'phonk' aesthetic. "
        "Subjects are mythological or biblical (angels, demons, knights) in dynamic, frozen poses. "
        "Include subtle textural elements like vintage paper grain, slight lo-fi noise, or a vignette to enhance the moody, retro-digital fusion look."
    ),
    "byzantine_orthodox": (
        "traditional Byzantine Orthodox icon of Christ Pantocrator enthroned, Eastern Orthodox iconography style, medieval Byzantine painting, gold halo and accents, flat symbolic perspective, reverse perspective, solemn and majestic"
    ),
    "biblical_epic": (
        "Direct view of a classical High Renaissance religious oil painting itself, filling the entire frame with no borders, no frame, no wall, no canvas edges, "
        "no photographic realism of a physical artwork on display — we are seeing the painted surface directly. "
        "In the authentic style of masters like Raphael, Michelangelo, Leonardo da Vinci or Titian: elderly dignified biblical figure (God the Father, prophet, or saint) "
        "with long flowing white beard, wise serene expression, gentle luminous golden halo, wearing rich flowing robes in warm earth tones (deep red, emerald green, golden ochre). "
        "Background is soft luminous sky with ethereal clouds and gentle heavenly glow. "
        "Use classic Renaissance techniques: delicate sfumato blending, soft diffused lighting from above, warm harmonious palette with golden highlights, visible oil paint brushstrokes, "
        "subtle impasto texture, fine craquelure, and painterly surface qualities throughout. "
        "Reverent, monumental composition, timeless sacred atmosphere of divine grace and spiritual serenity. "
        "Strictly 2D painted artwork feel — never a realistic photograph of a framed painting, never show any physical object context, edges, or gallery setting."
    ),
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
        "Subtle scientific holographic overlays float gently in the space around the subject: "
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

# TODO
@router.post('/fix-scene-image-prompt')
async def fix_scene_image_prompt(request: FixImagePrompt):

    return
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
    logger.debug("Fixed prompt: %s", fixed_prompt)
    return {"fixed_prompt": fixed_prompt}


class FixVideoPrompt(BaseModel):
    image_prompt: Optional[str]
    video_prompt: str

# TODO
@router.post('/fix-scene-video-prompt')
async def fix_scene_video_prompt(request: FixVideoPrompt):
    return
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
    logger.debug("Fixed prompt: %s", fixed_prompt)
    return {"fixed_prompt": fixed_prompt}