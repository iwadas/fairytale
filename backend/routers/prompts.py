import os  # Added missing import
from openai import OpenAI
import instructor
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Optional
import json  # Added for debug logging

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
open_ai_client = instructor.from_openai(OpenAI(api_key=OPENAI_API_KEY))

class KeyEvent(BaseModel):
    time: str
    event: str
    emotional_shift: Optional[str] = None

class Character(BaseModel):
    name: str
    prompt: str

class Location(BaseModel):
    name: str
    prompt: str

class StoryData(BaseModel):
    title: str
    period: str
    summary: str
    central_conflict: str
    themes: List[str]
    psychological_core: str
    key_events: List[KeyEvent]
    main_characters: List[Character]
    locations: List[Location]
    tone: str

def gather_story_data(prompt: str) -> StoryData: 
    messages = [
        {
            "role": "system",
            "content": """
            You are an expert true-crime researcher and story analyst.
            Your task is to collect and summarize *all relevant factual and emotional information*
            about a historical or true-crime event, preparing it for cinematic scriptwriting later.

            - Be objective and fact-based but emotionally aware.
            - Your tone should feel like a detailed briefing for a documentary screenwriter.
            - Do NOT write narration or script dialogue yet.
            - Organize your findings clearly and logically.

            The output MUST be valid JSON and follow the given schema strictly.
            """
        },
        {
            "role": "user",
            "content": (
                "Research and summarize the crime or event described below.\n\n"
                "--- INPUT ---\n"
                f"{prompt}\n\n"
                "--- OUTPUT REQUIREMENTS ---\n"
                "Return your findings as a single JSON object with these keys:\n\n"
                "{\n"
                '    "title": "string - short title of the event",\n'
                '    "period": "string - e.g., \\"1996, Lakewood, Oregon\\"",\n'
                '    "summary": "string - concise overview of what happened and why it\'s significant",\n'
                '    "central_conflict": "string - what drives the story (e.g., betrayal, revenge, corruption)",\n'
                '    "themes": ["string", "string"],\n'
                '    "psychological_core": "string - what emotional or moral question the story explores",\n'
                '    "key_events": [\n'
                "        {\n"
                '            "time": "string - e.g., \\"March 12, 1996\\"",\n'
                '            "event": "string - what happened",\n'
                '            "emotional_shift": "string - how tension or emotion changes here"\n'
                "        }\n"
                "    ],\n"
                '    "main_characters": [\n'
                "        {\n"
                '            "name": "string",\n'
                '            "prompt": "string - short backstory and their motivation"\n'
                "        }\n"
                "    ],\n"
                '    "locations": [\n'
                "        {\n"
                '            "name": "string",\n'
                '            "prompt": "string - why this place matters emotionally or narratively"\n'
                "        }\n"
                "    ],\n"
                '    "tone": "string - e.g., dark, investigative, suspenseful"\n'
                "}\n\n"
                "⚙️ Notes:\n"
                "- Keep the output factual — avoid cinematic language or creative expansion.\n"
                "- Include only relevant people and places (don't invent new ones unless absolutely necessary for context).\n"
                "- Keep descriptions concise but vivid.\n"
                "- If any information is unknown, state `\"unknown\"`."
            )
        }
    ]
    response = open_ai_client.chat.completions.create(
        model="gpt-4o-mini",
        response_model=StoryData,  # Corrected response model
        messages=messages
    )

    # Debug: Log the AI response
    print("DEBUG: gather_story_data response:")
    print(json.dumps(response.model_dump(), indent=2))

    return response

class VoiceoverSegment(BaseModel):
    start_time: float
    duration: float
    text: str

class VoiceoverTimeline(BaseModel):
    title: str
    total_duration: float
    segments: List[VoiceoverSegment]

def generate_voiceovers(story_data: StoryData, film_duration: float) -> VoiceoverTimeline:
    target_duration = film_duration * 0.9  # Target 80% of film_duration
    messages = [
        {
            "role": "system",
            "content": f"""
            You are a professional documentary voiceover scriptwriter.
            Your task is to first craft a cinematic, emotionally resonant narration of the story — 
            and then format it into a timed voiceover timeline that fits ~90% (other 10% are pauses) of the total film duration ({film_duration}s).

            ⚡️ APPROACH OVERVIEW:
            - **Step 1:** Tell the story naturally, like a documentary narrator. Make it emotionally rich and immersive.
            - **Step 2:** Condense it to fit into {target_duration}s of actual speaking + short pauses.
            - **Step 3:** Split it into a structured voiceover timeline (segments with start_time, duration, and text).

            🎯 OBJECTIVE:
            - Final voiceover duration (speaking + pauses) = ~90% of {film_duration}s.
            - Use natural pacing: **word_count * 0.55s** per segment (≈ 2 words/sec).
            - Include short 1–2s pauses between segments to allow emotional breathing and visual transitions.
            - Focus only on the most compelling and story-defining parts if time is limited.

            🎬 STYLE:
            - The tone should feel cinematic, human, and emotionally grounded — not like a summary.
            - Think of an experienced narrator guiding the viewer through emotion, revelation, and reflection.
            - Avoid scene directions or camera cues — focus on spoken storytelling.

            ⚙️ TECHNICAL CONSTRAINTS:
            - Each segment’s duration = word_count * 0.55s (natural pacing).
            - Aim in short segments - not more than 2 sentences.
            - Round all times to 0.5s increments.
            - No overlaps: seg[i].end_time < seg[i+1].start_time.
            - Include 1–2s pauses between segments (reflected in start_time gaps).
            - Verify total duration = 90% of film_duration. Adjust text if not.
            - Output JSON only (no explanations).

            🔍 EXAMPLE WORKFLOW (INTERNAL):
            1. Write a short cinematic narration of the full story.
            2. Edit it to fit into {target_duration}s using the pacing rule (≈ 2 words/sec).
            4. Assign timings and pauses, verify total length and no overlaps.
            5. Output in the final JSON structure below.

            --- FINAL OUTPUT FORMAT ---
            {{
                "title": "string - same as story_data.title",
                "total_duration": {film_duration},
                "segments": [
                    {{
                        "start_time": float (e.g., 0.0, rounded to 0.5s),
                        "duration": float (word_count * 0.55s),
                        "text": "string - narration (cinematic and concise)"
                    }}
                ]
            }}
            """
        },
        {
            "role": "user",
            "content": (
                f"Tell a cinematic documentary story based on the following structured data, then format it "
                f"into a verified, time-aligned voiceover timeline lasting approximately {target_duration} seconds "
                f"(≈80% of total film duration {film_duration}s).\n\n"
                "--- INPUT STORY DATA ---\n"
                f"{story_data.model_dump_json(indent=2)}\n\n"
                "--- OUTPUT REQUIREMENTS ---\n"
                "- Use natural pacing: Duration = word_count * 0.55s.\n"
                "- Total voiceover = 90% of film duration.\n"
                "- Include 1–2s pauses between segments for emotional rhythm.\n"
                "- Choose only the most important, captivating story parts if time is limited.\n"
                "- Round all times to nearest 0.5s.\n"
                "- Verify total duration and no overlaps before output.\n\n"
                "--- OUTPUT JSON FORMAT ---\n"
                "{\n"
                '    "title": "string - same as story title",\n'
                f'    "total_duration": {film_duration},\n'
                '    "segments": [\n'
                "        {\n"
                '            "start_time": float (rounded to 0.5s),\n'
                '            "duration": float (word_count * 0.55s),\n'
                '            "text": "cinematic narration text"\n'
                "        }\n"
                "    ]\n"
                "}\n\n"
                "After generating the story, divide it naturally into segments and assign proper timings.\n"
                "Ensure total speaking - 90%, pauses - 10% of film_duration and no overlaps."
            )
        }
    ]
    response = open_ai_client.chat.completions.create(
        model="gpt-5-mini",
        response_model=VoiceoverTimeline,
        messages=messages
    )

    # Debug: Log the AI response
    print("DEBUG: generate_voiceovers response:")
    print(json.dumps(response.model_dump(), indent=2))

    return response

class Scene(BaseModel):
    scene_number: int
    duration: float
    scene_type: Optional[str] = None
    image_prompt: str
    video_prompt: str

class SceneList(BaseModel):
    title: str
    total_duration: float
    scenes: List[Scene]

def generate_scenes(story_data: StoryData, voiceover_timeline: VoiceoverTimeline) -> SceneList:
    messages = messages = [
        {
            "role": "system",
            "content": """
            You are a professional documentary scene designer.
            Your task is to transform the voiceover timeline and story data into a continuous, cinematic sequence of visual scenes that perfectly accompany the narration.

            🎯 PRIMARY GOALS:
            - Create a complete list of scenes covering the entire film duration (≈ total_duration from the voiceover timeline).
            - Each scene corresponds closely to what the narrator is saying at that moment.
              ➤ If the narrator mentions “a storm rising,” show visual imagery of that storm or its emotional equivalent.
              ➤ If the narrator reflects on the past, show related memories, artifacts, or symbolic visuals.
            - The visuals must feel synchronized with the voiceover — never detached or generic.

            🕒 TIMING & STRUCTURE:
            - There is NO `start_time` or `end_time` per scene; those will be inferred later.
            - However, you must ensure that the **sum of all scene durations = total film duration (±1s)**.
            - When the voiceover pauses or ends before the total film duration:
              ➤ Fill the remaining time with short atmospheric visuals (e.g., “black screen pause,” “slow fade through mist,” “ambient landscape stillness”).
              ➤ Use such filler scenes sparingly — only for pacing or emotional breathing room, not as fillers for every gap.
            - Average scene duration: 3-8 seconds - IMPORTANT.
            - Adjust shot length dynamically:
              ➤ Shorter for rapid narration or intense moments.
              ➤ Longer for emotional or reflective narration.

            🎥 STYLE & CONTENT:
            - Match each scene directly to the voiceover's emotional and narrative content.
            - Use varied, cinematic shot types: wide establishing shots, close-ups, handheld realism, drone sweeps, or archival footage.
            - Emphasize storytelling through imagery — every shot should reveal something or heighten mood.
            - Include natural transitions: fade, dissolve, match cut, camera pan, etc.
            - Keep realism, tone, and period consistent with the story.

            ⚙️ SCENE FORMAT:
            Each scene should include:
            - scene_number: integer (1, 2, 3, …)
            - duration: float (3-8 seconds)
            - image_prompt: detailed visual description for AI image/video generation (composition, lighting, setting, emotion)
            - video_prompt: brief note about camera movement or visual tone
            - optional scene_type (if useful): e.g., “archival,” “dramatic_reenactment,” “ambient_pause,” “black_screen_pause”

            📏 VERIFICATION RULES:
            - Total of all scene durations ≈ voiceover_timeline.total_duration (100% of film runtime).
            - The number and pacing of scenes should reflect the rhythm of the narration.
            - Avoid leaving large unfilled gaps — use pauses only where they enhance impact.
            - Never create fewer scenes than needed to visually support every voiceover segment.

            """
        },
        {
            "role": "user",
            "content": (
                "Generate a cinematic storyboard based on the provided story and narration.\n\n"
                "--- STORY DATA ---\n"
                f"{story_data.model_dump_json(indent=2)}\n\n"
                "--- VOICEOVER TIMELINE ---\n"
                f"{voiceover_timeline.model_dump_json(indent=2)}\n\n"
                "--- OUTPUT JSON FORMAT ---\n"
                "{\n"
                '    "title": "string - same as story title",\n'
                f'    "total_duration": {voiceover_timeline.total_duration},\n'
                '    "scenes": [\n'
                "        {\n"
                '            "scene_number": integer,\n'
                '            "duration": float (3–7 typical),\n'
                '            "image_prompt": "detailed description tied to narration",\n'
                '            "video_prompt": "camera movement or tone (e.g., slow pan, handheld, fade)",\n'
                '            "scene_type": "optional string (e.g., archival, ambient_pause, black_screen_pause)"\n'
                "        }\n"
                "    ]\n"
                "}\n\n"
                "--- CRITICAL REQUIREMENTS ---\n"
                "- Each scene must visually align with the current voiceover content.\n"
                "- Total duration of all scenes = total film duration (±1s).\n"
                "- If gaps exist between voiceover moments, fill with cinematic pauses or transitions — but use them minimally.\n"
                "- The storyboard must feel seamless, as if a viewer were watching the finished film.\n"
            )
        }
    ]

    response = open_ai_client.chat.completions.create(
        model="gpt-5-mini",
        response_model=SceneList,
        messages=messages
    )

    # Debug: Log the AI response
    print("DEBUG: generate_scenes response:")
    print(json.dumps(response.model_dump(), indent=2))

    return response

class CharacterOut(BaseModel):
    name: str
    prompt: str

class PlaceOut(BaseModel):
    name: str
    prompt: str

class SceneOut(BaseModel):
    scene_number: int
    duration: int
    image_prompt: str
    video_prompt: str

class VoiceoverOut(BaseModel):
    text: str
    start_time: float
    duration: float

class ProjectOut(BaseModel):
    characters: List[CharacterOut]
    places: List[PlaceOut]
    scenes: List[SceneOut]
    voiceovers: List[VoiceoverOut]

def get_full_project(story_data: StoryData, voiceover_timeline: VoiceoverTimeline, scene_list: SceneList) -> ProjectOut:
    messages = [
        {
            "role": "system",
            "content": """
            You are a cinematic production director assistant.
            Your task is to assemble a complete video project structure by combining story data, voiceovers, and scenes into a unified output.

            🎯 Objective
            - Merge all previous data into a single structured `ProjectOut` object.
            - Ensure the project can be directly used for video generation.
            - The structure must align with the specified model schema.

            ⚙️ Assembly Rules
            - Scene numbers correspond to their sequential order.
            - Each scene includes:
            - `duration`: rounded seconds
            - `image_prompt` and `video_prompt` directly from scene data
            - `character_ids`: link to characters mentioned in the story segment
            - `places_ids`: link to relevant locations for that scene
            - Voiceovers:
            - Use data from the `voiceover_timeline`
            - Calculate `start_time` cumulatively based on order and text length
            - Ensure no overlap in timing (start of next = end of previous)
            - Keep names and prompts consistent across all sections.
            - Ensure continuity and logical connections (characters/places appear where appropriate).
            - Output **only valid JSON** matching the model structure.

            ⚠️ Important
            - Do not invent new entities; use only ones already present in story_data.
            - Scene durations and voiceover timings should be coherent (no negative gaps, no overlap).
            - Ensure total voiceover and scene durations roughly align.
            """
        },
        {
            "role": "user",
            "content": (
                "Combine the following inputs into one cohesive project output.\n\n"
                "--- STORY DATA ---\n"
                f"{story_data.model_dump_json(indent=2)}\n\n"
                "--- VOICEOVER TIMELINE ---\n"
                f"{voiceover_timeline.model_dump_json(indent=2)}\n\n"
                "--- SCENE LIST ---\n"
                f"{scene_list.model_dump_json(indent=2)}\n\n"
                "--- OUTPUT FORMAT ---\n"
                "{\n"
                '    "characters": [\n'
                "        {\n"
                '            "name": "string - character name",\n'
                '            "prompt": "string - short description or visual cue for this character"\n'
                "        }\n"
                "    ],\n"
                '    "places": [\n'
                "        {\n"
                '            "name": "string - place name",\n'
                '            "prompt": "string - visual or atmospheric prompt for the location"\n'
                "        }\n"
                "    ],\n"
                '    "scenes": [\n'
                "        {\n"
                '            "scene_number": "int - sequential order",\n'
                '            "duration": "int - rounded seconds",\n'
                '            "image_prompt": "string - detailed image prompt",\n'
                '            "video_prompt": "string - cinematic camera or movement style",\n'
                "        }\n"
                "    ],\n"
                '    "voiceovers": [\n'
                "        {\n"
                '            "text": "string - narration text",\n'
                '            "start_time": "float - cumulative start time in seconds"\n'
                '            "duration: float word_count * 0.55'
                "        }\n"
                "    ]\n"
                "}"
            )
        }
    ]
    response = open_ai_client.chat.completions.create(
        model="gpt-4o-mini",
        response_model=ProjectOut,
        messages=messages
    )

    # Debug: Log the AI response
    print("DEBUG: get_full_project response:")
    print(json.dumps(response.model_dump(), indent=2))

    return response