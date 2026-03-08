from typing import Dict, List, Callable, Optional, Any
from pydantic import BaseModel, Field
import math
import json
# Assuming AI.llm import exists in your environment
from AI.llm import LLM
import asyncio
import re

# ==========================================
# CONFIGURATION & MODELS
# ==========================================
# (AVAILABLE_STYLES dict remains exactly the same as before)
AVAILABLE_STYLES = {
    "macro_shatter": {
        "use_case": "Use for hyper-fixation, intrusive thoughts, or breaking down a specific microscopic detail of human behavior. Focuses on extreme, uncomfortable close-ups.",
        "technical_prompt": (
            "Extreme macro photography, tight framing on a single object. "
            "Everything must be sharp, fractured, and splintered geometric forms. "
            "Materials strictly limited to: Polished Black Obsidian, Liquid Chrome/Mercury, Iridescent Oil Slick, Smoked Deep Crimson Glass, Vantablack, or Matte Bone White. "
            "Background must be a blurred abstract geometric pattern. "
            ", hyper-realistic 3D render, fractured dark-aesthetic sculpture, flawless ultra-reflective surfaces, stark chiaroscuro studio lighting, piercing crimson and cold cyan rim lights, engulfing pitch-black shadows, extreme macro photography depth of field, Octane render, raytracing, heavy caustics, psychological thriller mood, 8k"
        )
    },
    "liminal_void": {
        "use_case": "Use for themes of isolation, hopelessness, emotional distance, or feeling incredibly small compared to a manipulator or a grand psychological concept.",
        "technical_prompt": (
            "Wide-angle monolithic scale, tiny subject surrounded by massive, infinite, and overwhelming space. "
            "Everything must be sharp, fractured, and splintered geometric forms. "
            "Materials strictly limited to: Polished Black Obsidian, Liquid Chrome/Mercury, Iridescent Oil Slick, Smoked Deep Crimson Glass, Vantablack, or Matte Bone White. "
            "Background is an endless geometric abyss. "
            ", hyper-realistic 3D render, fractured dark-aesthetic sculpture, flawless ultra-reflective surfaces, stark chiaroscuro studio lighting, piercing crimson and cold cyan rim lights, engulfing pitch-black shadows, deep focus, Octane render, raytracing, heavy caustics, psychological thriller mood, 8k"
        )
    },
    "fluid_distortion": {
        "use_case": "Use for gaslighting, loss of identity, shifting realities, or toxic influence seeping into a situation. Focuses on melting, rippling, or warping elements.",
        "technical_prompt": (
            "Warped, rippling, and melting composition. Hard shapes dissolving into viscous liquids. "
            "Everything must be sharp, fractured, and splintered geometric forms interacting with fluid dynamics. "
            "Materials strictly limited to: Polished Black Obsidian, Liquid Chrome/Mercury, Iridescent Oil Slick, Smoked Deep Crimson Glass, Vantablack, or Matte Bone White. "
            "Background must be a shifting abstract geometric setting. "
            ", hyper-realistic 3D render, fractured dark-aesthetic sculpture, flawless ultra-reflective surfaces, stark chiaroscuro studio lighting, piercing crimson and cold cyan rim lights, engulfing pitch-black shadows, macro photography depth of field, Octane render, raytracing, heavy caustics, psychological thriller mood, 8k"
        )
    },
    "claustrophobic_cage": {
        "use_case": "Use for anxiety, feeling trapped, overthinking, or being cornered in a toxic dynamic. Focuses on dense, overlapping obstacles blocking the view.",
        "technical_prompt": (
            "Cramped framing, dense overlapping foreground elements acting like bars or cages, blocking the camera's view of the subject. "
            "Everything must be sharp, fractured, and splintered geometric forms. "
            "Materials strictly limited to: Polished Black Obsidian, Liquid Chrome/Mercury, Iridescent Oil Slick, Smoked Deep Crimson Glass, Vantablack, or Matte Bone White. "
            "Background must be a dense, heavy geometric labyrinth. "
            ", hyper-realistic 3D render, fractured dark-aesthetic sculpture, flawless ultra-reflective surfaces, stark chiaroscuro studio lighting, piercing crimson and cold cyan rim lights, engulfing pitch-black shadows, narrow depth of field, Octane render, raytracing, heavy caustics, psychological thriller mood, 8k"
        )
    },
    "suspended_chaos": {
        "use_case": "Use for sudden realizations, trauma, emotional outbursts, or snapping under pressure. Focuses on explosive, frozen-in-time destruction.",
        "technical_prompt": (
            "Zero-gravity time-freeze, explosive debris, shards suspended mid-air in a chaotic but beautiful arrangement. "
            "Everything must be sharp, fractured, and splintered geometric forms. "
            "Materials strictly limited to: Polished Black Obsidian, Liquid Chrome/Mercury, Iridescent Oil Slick, Smoked Deep Crimson Glass, Vantablack, or Matte Bone White. "
            "Background is a shattered abstract geometric environment. "
            ", hyper-realistic 3D render, fractured dark-aesthetic sculpture, flawless ultra-reflective surfaces, stark chiaroscuro studio lighting, piercing crimson and cold cyan rim lights, engulfing pitch-black shadows, dynamic focal length, Octane render, raytracing, heavy caustics, psychological thriller mood, 8k"
        )
    }
}

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


class SceneIdea(BaseModel):
    style: str = Field(
        description="Name of the best suiting style for this generation.",
        json_schema_extra={"enum": list(AVAILABLE_STYLES.keys())}
    )
    idea: str = Field(description="Brief description of the visual scene, concise—focus on the core visual subject and environment")
    reasoning: str = Field(description="Why visual fits the context")

class SceneIdeasResponse(BaseModel):
    scenes: List[SceneIdea]

class ScenePromptsResponse(BaseModel):
    image_prompt: str = Field(description="Highly descriptive image prompt including subject, environment, lighting, and style integration.")
    video_prompt: str = Field(description="Motion-focused video prompt. Format: [Camera Movement], [Subject Movement], [Speed/Vibe]")

class HarmonizedScene(BaseModel):
    scene_id: int = Field(description="The exact ID of the scene.")
    video_prompt: str = Field(description="The harmonized video prompt.")

class HarmonizedSequenceResponse(BaseModel):
    harmonized_scenes: List[HarmonizedScene]


# ==========================================
# ASYNC WORKER FUNCTIONS
# ==========================================
async def _expand_single_prompt(llm_client: 'LLM', local_idx: int, idea_obj: SceneIdea) -> Dict[str, Any]:
    """Agent 2: Expands a single idea into full prompts."""
    chosen_style = idea_obj.style 
    technical_instructions = AVAILABLE_STYLES.get(chosen_style, {}).get('technical_prompt', '')

    agent_2_messages = [
        {
            "role": "system",
            "content": "You are an expert AI Prompt Engineer specializing in Text-to-Image (Nano Banana Pro) and Image-to-Video models (e.g. Veo Pro, Sora Pro, Kling AI, Seedance)."
        },
        {
            "role": "user",
            "content": (
                "I have a raw scene idea:\n"
                f"idea: {idea_obj.idea}\n"
                f"reasoning: {idea_obj.reasoning}\n"
                f"style: {technical_instructions}\n\n"
                "Your task is to take a rough scene idea and its assigned visual styles, and expand it into two specific prompts.\n"
                "1. 'image_prompt': Must be highly descriptive. Include the subject, environment, lighting, atmosphere, and explicitly integrate the provided styles.\n"
                "2. 'video_prompt': Suitable for the AI image to video generator (Format: [Camera Movement], [Subject Movement], [Speed/Vibe]). Keep the video prompt focused on motion. Do not include information about style, lighting since the AI already has an image reference. Keep subject movement micro-focused. Instead of 'man running across a field', use 'wind blowing through grass, man's hair gently swaying'. Isolate motion to one or two elements."
            )
        }
    ]

    prompts_response = await llm_client.generate(
        messages=agent_2_messages,
        response_format=ScenePromptsResponse,
        temperature=0.5 
    )
    
    return {
        "local_id": local_idx,
        "style": idea_obj.style,
        "idea": idea_obj.idea,
        "reasoning": idea_obj.reasoning,
        "image_prompt": prompts_response.image_prompt,
        "video_prompt": prompts_response.video_prompt
    }


async def _process_script_part(
    i: int, 
    script_part: Dict[str, Any], 
    llm_client: 'LLM', 
    script: str, 
    total_parts: int, 
    semaphore: asyncio.Semaphore,
    progress_callback: Optional[Callable]
) -> Dict[str, Any]:
    """Handles Agent 1, Agent 2, and Agent 3 for a single script part."""
    
    # The semaphore ensures we don't bombard the LLM API and get rate-limited
    async with semaphore:
        num_scenes = math.ceil(script_part['duration'] / 1.5)
        
        if progress_callback:
            await progress_callback(status="in_progress", message=f"🎬 Part {i+1}/{total_parts}: Agent 1 brainstorming...")

        # --- AGENT 1: IDEA GENERATION ---
        agent_1_styles_formatted = "\n".join([f"- {name}: {data['use_case']}" for name, data in AVAILABLE_STYLES.items()])
        

        agent_1_messages = [
            {
                "role": "system",
                "content": f"You are a highly creative Visual Director for a video production pipeline. Your job is to brainstorm short, high-impact scene ideas for specific parts of a script. You do not need to worry about character or location consistency. We are generating many short, rapid-fire scenes to cherry-pick the best ones later - so try to use variety of ideas. Here is full script just for the context:\n\n{script}"
            },
            {
                "role": "user",
                "content": (
                    f"Generate EXACTLY {num_scenes} raw visual concepts for this sentence: \"{script_part['text']}\".\n\n"
                    "For each visual concept specify:\n"
                    "- \"idea\" - Brief description of the visual scene, concise—focus on the core visual subject and environment\n"
                    "- \"style\" - Name of the best suiting style for this generation\n"
                    "- \"reasoning\" - Why visual fits the context\n\n"
                    "Diversity Rule: Do not use the same style more than 3 Times in a row.\n"
                    "Available styles:\n"
                    f"{agent_1_styles_formatted}"       
                )
            }
        ]

        ideas_response = await llm_client.generate(messages=agent_1_messages, response_format=SceneIdeasResponse, temperature=0.8)

        # --- AGENT 2: PROMPT EXPANSION (Concurrent) ---
        if progress_callback:
            await progress_callback(status="in_progress", message=f"🎨 Part {i+1}/{total_parts}: Agent 2 expanding prompts...")

        # Run all Agent 2 expansions for this specific part simultaneously
        agent_2_tasks = [
            _expand_single_prompt(llm_client, local_idx, idea_obj)
            for local_idx, idea_obj in enumerate(ideas_response.scenes)
        ]
        local_scenes_for_part = await asyncio.gather(*agent_2_tasks)

        # --- AGENT 3: CAMERA MOVEMENT HARMONIZATION ---
        if progress_callback:
            await progress_callback(status="in_progress", message=f"🎥 Part {i+1}/{total_parts}: Agent 3 harmonizing flow...")

        minimal_scenes_for_agent_3 = [
            {"id": scene["local_id"], "idea": scene["idea"], "video_prompt": scene["video_prompt"]}
            for scene in local_scenes_for_part
        ]

        agent_3_messages = [
            {
                "role": "system",
                "content": (
                    "You are a Master Video Editor and Cinematographer. Your goal is to review a short sequence of AI video generation prompts and harmonize their camera movements to create a smooth, hypnotic flow.\n"
                    "### STRICT CAMERA VOCABULARY\n"
                    "You MUST select the camera movement from this exact list:\n"
                    "- Static: No camera movement, focus purely on subject motion.\n"
                    "- Pan: Horizontal rotation.\n"
                    "- Nodal Pan: Panning without changing the camera's physical position (great for wide landscapes).\n"
                    "- Tilt: Vertical rotation.\n"
                    "- Pan and Tilt: Combined diagonal/sweeping rotation.\n"
                    "- Track/dolly: Moving forward or backward through space.\n"
                    "- Lateral track: Moving perfectly sideways (great for hypnotic side-scrolling).\n"
                    "- Crane / pedestal: Moving strictly up or down in space.\n"
                    "- Handheld: Adds subtle, gritty, realistic shake.\n"
                    "- Stabilized: Ultra-smooth, gimbal-like motion.\n\n"
                    "### RULES FOR SMOOTHING\n"
                    "1. MATCHING MOMENTUM: If consecutive scenes share a similar vibe, match or naturally sequence their camera movements. (e.g., A 'Lateral track' right flows perfectly into a 'Pan' right).\n"
                    "2. LOGICAL LIMITS: Do not force a camera movement if it feels physically impossible for the described image. If matching the previous scene's movement breaks the current scene, use 'Static' or 'Stabilized' as a neutral reset.\n"
                    "3. ISOLATION: Separate the camera movement from the subject action."
                )
            },
            {
                "role": "user",
                "content": (
                    "Here is the short sequence of scenes in chronological order:\n"
                    f"{json.dumps(minimal_scenes_for_agent_3, indent=2)}\n\n"
                    "Analyze the camera movements, harmonize them using ONLY the approved vocabulary, and output the updated sequence."
                )
            }
        ]

        harmonization_response = await llm_client.generate(
            messages=agent_3_messages,
            response_format=HarmonizedSequenceResponse,
            temperature=0.2
        )

        # Update local scenes
        harmonized_dict = {scene.scene_id: scene.video_prompt for scene in harmonization_response.harmonized_scenes}

        for scene in local_scenes_for_part:
            scene_id = scene["local_id"]
            if scene_id in harmonized_dict:
                scene["video_prompt"] = harmonized_dict[scene_id]
            del scene["local_id"] # Cleanup

        return {
            "text": script_part["text"],
            "duration": script_part["duration"],
            "start_time": script_part["start_time"],
            "scenes": local_scenes_for_part
        }


# ==========================================
# MAIN GENERATION FUNCTION
# ==========================================
async def generate_scenes(
    llm_client: 'LLM', 
    script: str,
    splitted_script: List[Dict[str, Any]],
    progress_callback: Optional[Callable] = None,
    max_concurrent_parts: int = 5 # Adjust this based on your API tier limits
) -> List[Dict[str, Any]]:
    
    total_parts = len(splitted_script)
    
    # Semaphore restricts how many script parts process simultaneously
    semaphore = asyncio.Semaphore(max_concurrent_parts)
    
    # Create a task for every script part
    tasks = [
        _process_script_part(i, part, llm_client, script, total_parts, semaphore, progress_callback)
        for i, part in enumerate(splitted_script)
    ]
    
    # Execute all parts concurrently and wait for all to finish
    script_parts_with_scenes = await asyncio.gather(*tasks)

    if progress_callback:
        await progress_callback(status="complete", message="✅ Pipeline finished asynchronously!")

    # asyncio.gather returns results in the exact same order the tasks were passed in
    return list(script_parts_with_scenes)