from typing import Dict, List, Callable, Literal, Optional
from AI.llm import LLM
from pydantic import BaseModel, Field
import re
import json
import math
import asyncio

# --- HELPER FUNCTIONS REMAIN UNCHANGED ---
def estimate_duration(text: str) -> float:
    words_per_minute: float = 200.0
    chars_per_minute: float = 200.0 * 5
    words = len(text.split())
    chars = len(text.replace(" ", ""))
    seconds = round((words / words_per_minute * 60) + (chars / chars_per_minute * 60) / 2, 1)
    return seconds

def split_script(script: str) -> list:
    pattern = r'(<br>)'
    parts = re.split(pattern, script)
    sentences = []

    current_time = 0
    for part in parts:
        part = part.strip()
        if part and part != '<br>':
            duration = estimate_duration(part)
            sentences.append({
                "start_time": current_time,
                "text": part,
                "duration": duration,
            })
            current_time += duration
        elif part == '<br>':
            current_time += 0.5
            print("Split script into sentences with timing:")
    for sentence in sentences:
        print(f"Start: {sentence['start_time']}s, Duration: {sentence['duration']}s, Text: {sentence['text']}")
    return sentences

# --- NEW PYDANTIC MODELS ---

# Step 1: The Raw Concept
class ConceptScene(BaseModel):
    representation_type: Literal["Literal", "Metaphorical", "Abstract"] = Field(
        description="Is this scene Literal, Metaphorical, or Abstract?"
    )
    reasoning: str = Field(description="Why does this raw visual perfectly represent the script text?")
    raw_visual_concept: str = Field(
        description="The un-styled visual concept. Describe WHAT is happening and WHO/WHAT the subject is. DO NOT include lighting, camera, or specific aesthetic styles."
    )

class ConceptsResponse(BaseModel):
    scenes: List[ConceptScene]

# Step 2: The Styled Scene & Motion
class StyledScene(BaseModel):
    image_prompt: str = Field(
        description="The final visual description applying the strict geometric style rules to the raw concept. Highly detailed."
    )
    video_prompt: str = Field(
        description="Camera movement and action instructions based on the scene. Strict format: [Camera Movement], [Subject Movement], [Speed/Vibe]."
    )

class StyledScenesResponse(BaseModel):
    scenes: List[StyledScene]


# --- REFACTORED GENERATOR ---

async def generate_scenes(
    llm_client: LLM,
    script: str,
    splitted_script: List[Dict[str, any]],
    progress_callback: Optional[Callable] = None
) -> List[Dict[str, any]]:

    style = (
        "**VISUAL STYLE RULES (APPLY THESE TO THE RAW CONCEPT)**\n"
        "1. **Geometry:** Everything must be described as sharp, fractured, and splintered geometric forms.\n"
        "2. **Materials:** For every object, assign one of these: Polished Black Obsidian, Liquid Chrome/Mercury, Iridescent Oil Slick, Smoked Deep Crimson Glass, Vantablack, or Matte Bone White.\n"
        "3. **Environment:** Never leave the background empty. Describe a geometric/abstract version of the setting.\n\n"
        "Append this exactly to the end of the prompt: , hyper-realistic 3D render, fractured dark-aesthetic sculpture, flawless ultra-reflective surfaces, stark chiaroscuro studio lighting, piercing crimson and cold cyan rim lights, engulfing pitch-black shadows, macro photography depth of field, Octane render, raytracing, heavy caustics, psychological thriller mood, 8k"
    )

    # Phase 1: Director System Prompt (Idea Generation)
    director_system_message = {
        "role": "system",
        "content": (
            "You are an expert Director for Psychology and Philosophy video essays. "
            "Your ONLY job is to invent brilliant, striking visual metaphors for the provided script. "
            f"### FULL SCRIPT OVERVIEW:\n\"{script}\"\n\n"
            "Translate the script into raw visual concepts (Literal, Metaphorical, Abstract). "
            "Focus ONLY on the subjects, their actions, and the setting. Do NOT apply camera angles, lighting, or specific render styles. "
            "**NO TEXT ON SCREEN:** Never describe signs or words."
        )
    }

    # Phase 2: Art Director System Prompt (Stylization & Motion)
    art_director_system_message = {
        "role": "system",
        "content": (
            "You are an expert 3D Concept Artist and AI Video Cinematographer. "
            "Your job is to take a raw visual concept and translate it perfectly into a specific visual aesthetic, then write a motion prompt for it."
        )
    }

    script_parts_with_scenes = []

    for i, script_part in enumerate(splitted_script):
        if progress_callback:
            await progress_callback(
                status="in_progress",
                message=f"🎬 Conceptualizing part {i+1}/{len(splitted_script)}..."
            )

        num_scenes = math.ceil(script_part['duration'] / 3)

        # --- STEP 1: GENERATE CONCEPTS (The "Director") ---
        director_user_message = {
            "role": "user",
            "content": (
                f"**Generate exactly {num_scenes} raw visual concepts for this sentence:**\n"
                f"\"{script_part['text']}\"\n\n"
                "Make sure the concepts naturally progress from one to the next."
            )
        }

        concept_response = await llm_client.generate(
            messages=[director_system_message, director_user_message],
            response_format=ConceptsResponse
        )

        final_scenes_for_part = []

        # --- STEP 2: APPLY STYLE & MOTION (The "Art Director") ---
        if progress_callback:
            await progress_callback(
                status="in_progress",
                message=f"🎨 Applying style to part {i+1}/{len(splitted_script)}..."
            )

        for j, concept in enumerate(concept_response.scenes):
            
            # We give the Art Director the style rules and the raw concept to translate
            art_director_user_message = {
                "role": "user",
                "content": (
                    f"### RAW CONCEPT TO STYLIZE:\n"
                    f"Reasoning: {concept.reasoning}\n"
                    f"Raw Visual: {concept.raw_visual_concept}\n\n"
                    f"### STYLE INSTRUCTIONS:\n{style}\n\n"
                    "1. Translate the raw visual into a detailed `image_prompt` using the strict geometry and material rules.\n"
                    "2. Write a `video_prompt` for the AI video generator (Format: [Camera Movement], [Subject Movement], [Speed/Vibe]). Keep the video prompt focused purely on motion."
                )
            }

            styled_response = await llm_client.generate(
                messages=[art_director_system_message, art_director_user_message],
                response_format=StyledScenesResponse 
            )

            # Extract the single styled scene (we passed one concept in, we expect one styled scene out)
            styled_scene = styled_response.scenes[0]

            print(f"--- Part {i+1}, Scene {j+1} ---")
            print(f"Concept: {concept.raw_visual_concept}")
            print(f"Image Prompt: {styled_scene.image_prompt}")
            print(f"Video Prompt: {styled_scene.video_prompt}\n")

            final_scenes_for_part.append({
                "representation_type": concept.representation_type,
                "reasoning": concept.reasoning,
                "raw_visual_concept": concept.raw_visual_concept,
                "image_prompt": styled_scene.image_prompt,
                "video_prompt": styled_scene.video_prompt,
            })

        script_parts_with_scenes.append({
            "text": script_part["text"],
            "duration": script_part["duration"],
            "start_time": script_part["start_time"],
            "scenes": final_scenes_for_part
        })

    return script_parts_with_scenes