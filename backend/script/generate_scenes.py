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
    # ==============================
    # MACRO (Extreme Close-Ups & Portraits)
    # ==============================
    "macro_literal": {
        "use_case": "Use for extreme close-ups of specific physical actions or biological forms mentioned in the script (e.g., an eye twitching, a hand clenching).",
        "technical_prompt": (
            "Extreme macro photography, tight framing on a specific physical or biological subject from the script. "
            "STRICTLY NO literal text, typography, or spelled-out words. "
            "The subject must be highly recognizable but constructed entirely from non-organic materials. "
            "Materials strictly limited to: Polished Black Obsidian, Liquid Chrome/Mercury, Iridescent Oil Slick, Smoked Deep Crimson Glass, Vantablack, or Matte Bone White. "
            "Visual motif: pristine Matte Bone White being slowly overtaken by creeping Iridescent Oil Slick. "
            "Background is blurred deep shadow. "
            ", hyper-realistic 3D render, stark chiaroscuro studio lighting, piercing crimson and cold cyan rim lights (signaling aggression/manipulation), extreme macro photography depth of field, Octane render, raytracing, heavy caustics, psychological thriller mood, 8k. 1:1 aspect ratio."
        )
    },
    "macro_metaphor": {
        "use_case": "Use for extreme close-ups of symbolic objects representing an idea (e.g., a fractured mirror for identity, a heavy chain for addiction).",
        "technical_prompt": (
            "Extreme macro photography, tight framing on a symbolic object representing the script's core theme. "
            "STRICTLY NO literal text, typography, or spelled-out words. "
            "The symbolic object is physically grounded but surreal, fracturing or trapped by sharp geometric forms. "
            "Materials strictly limited to: Polished Black Obsidian, Liquid Chrome/Mercury, Iridescent Oil Slick, Smoked Deep Crimson Glass, Vantablack, or Matte Bone White. "
            ", hyper-realistic 3D render, flawless ultra-reflective surfaces, stark chiaroscuro studio lighting, flickering sodium yellow rim lights (signaling anxiety/paranoia), engulfing pitch-black shadows, shallow depth of field, Octane render, raytracing, heavy caustics, paranoia aesthetic, 8k. 1:1 aspect ratio."
        )
    },
    "macro_portrait": {
        "use_case": "Use to give a 'face' to the emotion without showing a real human. Best for representing the manipulator, the victim, or a shattered ego.",
        "technical_prompt": (
            "Extreme macro portrait photography of a faceless, humanoid feature—like a shattered porcelain mask, a featureless chrome silhouette, or a bone-white hand. "
            "STRICTLY NO literal text, real human skin, or recognizable eyes. "
            "Materials strictly limited to: Polished Black Obsidian, Liquid Chrome/Mercury, Iridescent Oil Slick, Smoked Deep Crimson Glass, Vantablack, or Matte Bone White. "
            "Visual motif: A pristine surface fracturing to reveal Vantablack underneath. "
            ", hyper-realistic 3D render, stark chiaroscuro studio lighting, clinical cold white rim light against pure pitch-black shadows (signaling isolation/depression), shallow depth of field, Octane render, raytracing, heavy caustics, psychological thriller mood, 8k. 1:1 aspect ratio."
        )
    },

    # ==============================
    # MEDIUM (Action & Power Dynamics)
    # ==============================
    "medium_dynamic": {
        "use_case": "Use for scenes showing interaction, power struggles, mirroring, or gaslighting between two entities.",
        "technical_prompt": (
            "Medium shot, dynamic composition showing two distinct abstract humanoid figures interacting in a power struggle. "
            "STRICTLY NO literal text or real humans. "
            "Figures must be constructed of contrasting materials: a towering Polished Black Obsidian figure casting a shadow over a fragile Matte Bone White or Smoked Crimson Glass figure. "
            ", hyper-realistic 3D render, striking contrast, stark chiaroscuro studio lighting, piercing crimson rim light against cold cyan fill (signaling conflict and dominance), heavy shadows, cinematic depth of field, Octane render, raytracing, psychological tension aesthetic, 8k. 1:1 aspect ratio."
        )
    },
    "kinetic_tethers": {
        "use_case": "Use to visually represent the hidden mechanisms of control, such as trauma bonding, emotional attachments, or manipulation.",
        "technical_prompt": (
            "Medium-close shot focusing entirely on the physical connection between two unseen points. "
            "STRICTLY NO literal text. "
            "Visual focus on kinetic elements of control: heavy Liquid Chrome chains, glowing Smoked Deep Crimson glass threads, or Iridescent Oil Slick bridging a gap. "
            "Background is an infinite dark void. "
            ", hyper-realistic 3D render, glowing internal light transmission, stark chiaroscuro lighting, flickering sodium yellow rim lights, deep focus, Octane render, raytracing, heavy caustics, clinical psychological mood, 8k. 1:1 aspect ratio."
        )
    },

    # ==============================
    # WIDE & TEXTURE (Environments / Pure Mood)
    # ==============================
    "wide_metaphor": {
        "use_case": "Use for themes of feeling trapped, cornered, or navigating a complex psychological issue (e.g., a maze, a cage, a giant monolithic obstacle).",
        "technical_prompt": (
            "Wide-angle monolithic scale, a tiny focal point surrounded by massive, overwhelming, metaphorical architecture (like a cage, labyrinth, or imposing monolith). "
            "STRICTLY NO literal text, typography, or spelled-out words. "
            "The tiny subject provides emotional scale against architecture entirely constructed from sharp, fractured, and splintered geometric forms. "
            "Materials strictly limited to: Polished Black Obsidian, Liquid Chrome/Mercury, Iridescent Oil Slick, Smoked Deep Crimson Glass, Vantablack, or Matte Bone White. "
            ", hyper-realistic 3D render, claustrophobic but vast composition, flawless ultra-reflective surfaces, stark chiaroscuro studio lighting, pure clinical white and Vantablack contrast (signaling hopelessness), deep focus, Octane render, raytracing, isolation aesthetic, 8k. 1:1 aspect ratio."
        )
    },
    "texture_abstract": {
        "use_case": "Use as b-roll for pure tension, transitions, shifting brain chemistry, or to represent the abstract 'feeling' of an emotional breakdown.",
        "technical_prompt": (
            "Frame completely filled with chaotic abstract fluid dynamics, shifting particles, and fracturing geometry. "
            "STRICTLY NO literal text or recognizable macroscopic/human objects. "
            "A pure study of tension: melting surfaces, warping viscous liquids, or sharp splinters. "
            "Materials strictly limited to: Polished Black Obsidian, Liquid Chrome/Mercury, Iridescent Oil Slick, Smoked Deep Crimson Glass, Vantablack, or Matte Bone White. "
            ", hyper-realistic 3D render, fluid simulation, stark chiaroscuro studio lighting, piercing crimson rim lights pulsing through engulfing pitch-black shadows, macro photography depth of field, Octane render, raytracing, heavy caustics, gaslighting aesthetic, 8k. 1:1 aspect ratio."
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
            current_time += 2.0
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
                "content": (
                    "You are a highly creative Visual Director for a video production pipeline. "
                    "Your job is to brainstorm short, high-impact scene ideas for specific parts of a script. "
                    "CRITICAL INSTRUCTION: You must build your visual concepts AROUND the provided available styles. "
                    "Do not brainstorm an idea and then assign a style. Instead, you must first select an available style, "
                    "read its 'use_case', and let those specific constraints dictate what happens in the scene. "
                    "You do not need to worry about character or location consistency. We are generating many short, "
                    "rapid-fire scenes to cherry-pick the best ones later - so try to use a variety of ideas. "
                    f"Here is the full script just for context:\n\n{script}"
                )
            },
            {
                "role": "user",
                "content": (
                    f"Generate EXACTLY {num_scenes} raw visual concepts for this sentence: \"{script_part['text']}\".\n\n"
                    "Available styles and their use cases:\n"
                    f"{agent_1_styles_formatted}\n\n"
                    "To ensure the style drives the visual, you MUST generate your output in this STRICT ORDER:\n"
                    "- \"style\": FIRST, pick the name of the most appropriate style from the available list.\n"
                    "- \"reasoning\": SECOND, explain why this style's specific 'use_case' fits the emotional or narrative context of the sentence.\n"
                    "- \"idea\": FINALLY, describe the visual scene. This description MUST strictly adhere to the style and use case you just selected. "
                    "Keep it concise—focus on the core visual subject and environment.\n\n"
                    "Diversity Rule: Do not use the same style more than 3 times in a row."
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