from typing import Dict, List, Optional, Literal
from AI.llm import LLM
from pydantic import BaseModel, Field
import re
import json
import asyncio

from script.generate_script import generate_script
from websocket import ConnectionManager
import math

def estimate_duration(text: str) -> float:
    words_per_minute: float = 200.0
    chars_per_minute: float = 200.0 * 5

    words = len(text.split())
    chars = len(text.replace(" ", ""))

    seconds = round(
        (words / words_per_minute * 60) + (chars / chars_per_minute * 60) / 2,
        1 # round to decimal place
    )
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

    # DEBUG
    print("Split script into sentences with timing:")
    for sentence in sentences:
        print(f"Start: {sentence['start_time']}s, Duration: {sentence['duration']}s, Text: {sentence['text']}")
    return sentences


class Scene(BaseModel):
    representation_type: Literal["Literal", "Metaphorical", "Abstract"] = Field(
        description="Is this scene showing exactly what is said (Literal), a symbolic representation (Metaphorical), or pure feeling (Abstract)?"
    )
    reasoning: str = Field(description="Why did you choose this visual for this specific text?")
    image_prompt: str = Field(description="The visual description. Detailed, focusing on lighting, composition, and subject.")
    video_prompt: str = Field(description="Camera movement and action instructions.")
class ScenesResponse(BaseModel):
    scenes: List[Scene]

async def generate_scenes(
    llm_client: LLM,
    splitted_script: List[Dict[str, any]],
    socket_manager: ConnectionManager,
    task_id: str
) -> List[Dict[str, any]]:

    # TODO: implement style choosing logic
    style = (
        "**VISUAL STYLE RULES (APPLY THESE TO EVERY SCENE)**\n"
        "1. **Geometry:** Everything must be described as sharp, faceted, low-poly geometric forms.\n"
        "2. **Materials:** For every object you describe, you MUST assign one of these specific materials:\n"
        "   - White Ceramic, Polished Black Obsidian, Matte Chocolate Brown, Brushed Gold, Grass Green, Glass.\n"
        "3. **Environment:** Never leave the background empty. Describe a geometric/abstract version of the setting.\n\n"
        ", hyper-realistic 3D render, faceted low-poly sculpture, "
        "flawless ultra-clean surfaces, dramatic moody studio lighting, "
        "warm orange rim lights, deep crisp shadows, macro photography depth of field, "
        "Octane render, raytracing, heavy caustics, 8k"
    )

    script_parts_with_scenes = []

    system_message = {
        "role": "system",
        "content": (
            "You are an expert AI Video Director and Cinematographer. "
            "Your expertise in making engaging visualizations for short-form videos - making it easy for viewers to understand and be amazed by the content. "
            "You are an expert Director for Psychology and Philosophy video essays. "
            "Translate the script into a mix of **Literal** and **Metaphorical** imagery.\n"
            "- **Literal:** Use when the script describes a specific, grounded action or biological process (e.g., 'The neurons fire').\n"
            "- **Metaphorical/Abstract:** Use when discussing feelings, concepts, or theories (e.g., 'The mind is a prison').\n"
            "- **Balance:** Do not make the video 100\\% abstract (boring) or 100\\% literal (cheesy). Mix them dynamically."
        )
    }

    def get_user_message_for_scene(scene_index: int) -> Dict[str, str]:

        previous_script_part = splitted_script[scene_index - 1] if scene_index > 0 else None
        next_script_part = splitted_script[scene_index + 1] if scene_index < len(splitted_script) - 1 else None

        script_context = (
            f"{
                (
                    f'Previous Script Part: {previous_script_part["text"]}\n\n'
                    f'Scenes used for previous part:\n{json.dumps(script_parts_with_scenes[scene_index - 1]["scenes"], indent=2)}\n\n'
                )
                if previous_script_part else ''
            }"
            f"Current Script Part (The one you need to generate scenes for): {splitted_script[scene_index]['text']}\n\n"
            f"Next Script Part: {next_script_part['text'] if next_script_part else 'N/A'}"
        )

        return {
            "role": "user",
            "content": (
                f"### CURRENT TASK\n"
                f"**Generate exactly {math.ceil(splitted_script[scene_index]['duration'] / 4)} scenes as a visual representation for sentence: {splitted_script[scene_index]['text']}**\n\n"

                "### NARATIVE FLOW\n"
                f"The previous scene ended looking like this:\n"
                f"\"{script_context}\"\n"
                f"(Start your new scene by matching this lighting/composition for a smooth cut.)\n\n"

                f"### STYLE\n"
                f"{style}\n"

                "### INSTRUCTIONS\n"
                "1. Generate visual scenes for this text.\n"
                "2. **Continuity:** Ensure the first scene transitions smoothly from the 'Previous Scene'.\n"
                "3. **Format:** JSON List of objects: {image_prompt, video_prompt}.\n"
                "**4. image_prompt:**\n"
                "- Describe the *content* and *composition* clearly.\n"
                "- Focus on what is physically visible (subjects, setting, perspective).\n"
                "- The description must be strong enough that a static image creates a 'wow' effect.\n\n"
                "**5. video_prompt:**\n"
                "**This prompt will be applied to the image generated from the image_prompt. So do not overexplain surrounding / objects, how they should look, or any other details not directly related to the action.**\n"
                "- STRICT FORMAT: `[Camera Movement], [Subject Movement], [Speed/Vibe].`\n"
                "- **Camera:** Use cool camera techniques (e.g., Orbit, Fly to birds view, Shaky camera, Drone camera flying through scene, Pan, Tilt, Zoom, Dolly, Static).\n"
                "- **Action:** Describe subtle movements (wind, blinking, walking). If no action, use 'Subtle natural movement' and **suitable** for scene context.\n"
                "- **Feasibility:** Ensure movements are realistic for AI video models.\n\n"
            )
        }

    
    for i, script_part in enumerate(splitted_script):
        await socket_manager.broadcast_json({
            "type": "create_project",
            "status": "in_progress",
            "task_id": task_id,
            "message": f"🎬 Generating scenes for part {i+1}/{len(splitted_script)}..."
        })

        respone = llm_client.generate(
            messages=[
                system_message,
                get_user_message_for_scene(i)
            ],
            response_format=ScenesResponse
        )

        # DEBUG
        for scene in respone.scenes:
            print(f"Generated scene for script part {i+1}:")
            print(f"Image Prompt: {scene.image_prompt}")
            print(f"Video Prompt: {scene.video_prompt}")

        script_parts_with_scenes.append({
            "text": script_part["text"],
            "duration": script_part["duration"],
            "start_time": script_part["start_time"],
            "scenes": [
                {
                    "image_prompt": scene.image_prompt,
                    "video_prompt": scene.video_prompt,
                    "representation_type": scene.representation_type,
                    "reasoning": scene.reasoning
                }
                for scene in respone.scenes
            ]
        })


    return script_parts_with_scenes


async def main():
    test_script = "When a man gets sleepy around the woman he loves, don't assume something is wrong. <br> Don't take it personally. For many men, feeling sleepy means feeling safe. <br> It means his body can finally relax. He doesn't have to stay alert anymore. <br> That's not boredom. That's trust"

    splitted_script = split_script(test_script)

    print("Final script parts with scenes:")
    for i, script_part in enumerate(splitted_script):
        print(f"Part {i+1}: {script_part}")

    await generate_scenes(
        llm_client=LLM(provider="xai", ai_model="grok-4-1-fast-reasoning"),
        splitted_script=splitted_script,
        socket_manager=ConnectionManager(),
        task_id="test_task_123"
    )

if __name__ == "__main__":
    asyncio.run(main())

