"""LLM prompts and structured-output models for the scene editor helpers.

Moved verbatim from the scenes router. The response-model class names and field
descriptions are part of the LLM request (instructor sends them as the tool
schema), so keep them stable.
"""

from typing import List, Optional

from pydantic import BaseModel, Field

# --- structured outputs -----------------------------------------------------------


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


class FixedPromptResponse(BaseModel):
    prompt: str = Field(description="The fixed prompt, with applied style adjustments, ready for image generation.")


class VideoPromptUpdate(BaseModel):
    new_video_prompt: str = Field(
        ...,
        description="The updated video prompt following the exact [Camera Movement], [Subject Movement], [Speed/Vibe] format."
    )


# --- message builders -------------------------------------------------------------


def image_prompts_messages(
    script: str, selected_voiceover_text_part: str, additional_info: Optional[str]
) -> list[dict[str, str]]:
    return [
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


# NOTE (audit B7): this hardcoded style replaces the request's ``style`` value.
FIX_IMAGE_PROMPT_STYLE = (
    "**VISUAL STYLE RULES (APPLY THESE TO THE RAW CONCEPT)**\n"
    "1. **Geometry:** Everything must be described as sharp, fractured, and splintered geometric forms.\n"
    "2. **Materials:** For every object, assign one of these: Polished Black Obsidian, Liquid Chrome/Mercury, Iridescent Oil Slick, Smoked Deep Crimson Glass, Vantablack, or Matte Bone White.\n"
    "3. **Environment:** Never leave the background empty. Describe a geometric/abstract version of the setting.\n\n"
    "Append this exactly to the end of the prompt: , hyper-realistic 3D render, fractured dark-aesthetic sculpture, flawless ultra-reflective surfaces, stark chiaroscuro studio lighting, piercing crimson and cold cyan rim lights, engulfing pitch-black shadows, macro photography depth of field, Octane render, raytracing, heavy caustics, psychological thriller mood, 8k"
)


def fix_image_prompt_messages(scene_prompt: str, style: str, style_power: Optional[float]) -> list[dict[str, str]]:
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
    return [system_message, user_message]


def fix_video_prompt_messages(
    current_idea: str,
    current_image_prompt: str,
    current_video_prompt: str,
    new_camera_movement: str,
    additional_info: Optional[str],
) -> list[dict[str, str]]:
    info_instruction = f"User provided additional adjustments: {additional_info}" if additional_info else "No additional user adjustments provided."

    return [
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
