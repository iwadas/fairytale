from math import floor
import os
import random  # Added missing import
from openai import OpenAI
import instructor
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json  # Added for debug logging
import re
import time
import copy

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
XAI_API_KEY = os.getenv('XAI_API_KEY')

open_ai_client = instructor.from_openai(OpenAI(api_key=XAI_API_KEY, base_url="https://api.x.ai/v1"))

ai_model = "grok-4-1-fast-reasoning"

class GatheredStoryData(BaseModel):
    gathered_data: str

def gather_story_data(topic: str) -> GatheredStoryData: 
    messages = [
        {
            "role": "system",
            "content": (
                "You are a factual researcher. Provide accurate, detailed, and structured information about the topic."
            )
        },
        {
            "role": "user",
            "content": f"Provide a detailed factual summary about the topic: {topic}. Your response must be between 500 and 800 words, using bullet points where appropriate. Focus on key historical facts, timeline, main figures, context, and notable outcomes or legends. Do not include fictional elements, reasoning, or commentary about your process."
        }
    ]
    response = open_ai_client.chat.completions.create(
        model=ai_model,
        response_model=GatheredStoryData,
        messages=messages
    )

    return response


class Story(BaseModel):
    script: str

def generate_story(topic: str, word_limit: int, story_data: str, reference_stories: str, persistant_characters: bool) -> Story:
    if story_data:
        context_instruction = (
            f"Base the story entirely on reference stories and gathered data:\n"
            f"Data:\n{story_data}\n\n"
            f"Example reference stories about the topic: \n{reference_stories}\n\n"
        )
    else:
        context_instruction = (
            f"Try to combine reference stories to make something engaging for viewer, "
            f"use most interesting parts but make sure it flows well together.\n"
            f"Reference Stories:\n{reference_stories}\n\n"
        )
    
    
    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert short-form storyteller for TikTok/Reels/Shorts. "
                "You write gripping, spoken-word narratives that hook instantly and never let go. "
                "Your style is conversational, emotional, and packed with rolling curiosity: "
                "every time you answer one question or resolve tension, you immediately open a new one. "
                "The listener should always be leaning in, desperate to hear what happens next."
            )
        },
        {
            "role": "user",
            "content": (
                f"Write a captivating spoken story about: {topic}\n\n"                
                f"{context_instruction}"
                f"Guidelines:\n"
                f"- Make the first 6 seconds extremely engaging to hook the listener immediately.\n"
                f"{'-' if persistant_characters else 'Do not include any persistant characters in the story.'}\n"
                f"- Vocabulary: 7th-grade reading level.\n"
                f"- Style: Conversational, suspenseful, and easy to follow.\n"
                f"- Start with a strong hook in the first 1-2 sentences to grab attention immediately.\n"
                f"- IMPORTANT: Length: Around {word_limit} (+/- 20) words (not counting tags).\n\n"
                f"- Use **rolling hooks** throughout: each time you resolve part of the story, spark a new sense of curiosity. "
                f"- Use natural **spoken rhythm**: (WHEN SUITABLE) use short sentences, occasional repetition, rhetorical questions, and brief pauses for dramatic tension.\n"
                f"- End with a **satisfying resolution** — either emotional (makes the listener feel) or reflective (makes them think)."
                f"🎭 **Emotion and pacing:**\n"
                f"Use the following tags to make the story sound like spoken performance — not too often, but enough to make it expressive.\n"
                f"- Alternate emotional tones (curiosity → excitement → tension → relief → reflection) to create an emotional rhythm that feels like a story, not a lecture.\n"
                f"- **SSML breaks (MANDATORY):** Use `<break time=\"1s\"/>` or `<break time=\"2s\"/>` to separate story beats. "
                f"Think of them as moments where a narrator would naturally pause — for suspense, reflection, or emotional shift. "
                f"Include at least **one break every 2–4 sentences**, and always after a major event, twist, or emotional moment. "
                f"These breaks are *required* and used to split the story into segments — so never skip them.\n"
                f"- **Emotion and tone tags (ONLY WHEN SUITABLE - DON'T OVERUSE):** Add emotional delivery cues like [happy], [sad], [excited], [fearful], [curious], [quietly], [whisper], [shout], etc. "
                f"These control *how* something is said, not *when* to pause. "
                f"Use them in addition to breaks, not instead of them.\n"
                f"Example:\n"
                f"[quietly]He reached for the old letter.<break time=\"1s\"/>\n"
                f"[curious]But why was it still sealed after all these years?<break time=\"2s\"/>\n"
                f"- **Use them meaningfully:** Include these tags only when they enhance the listener's emotional engagement.\n"
                f"  Think about how a storyteller would speak — add tags for emotional or dramatic parts, "
                f"but avoid overuse (around 1-2 emotion or pacing tags per short paragraph is ideal).\n\n"
                f"Output only the final story string, ready for text-to-speech."
            )
        }
    ]
    response = open_ai_client.chat.completions.create(
        model=ai_model,
        response_model=Story,
        messages=messages
    )

    return response


def estimate_speech_time(
    text: str,
    words_per_minute: float = 200.0,      # average adult speaking rate
    chars_per_minute: float = 200.0 * 5,      # ~5 chars per word * 150 wpm
):
    """
    Estimate how long it will take to read *text* aloud.

    1. Strip everything inside [square brackets].
    2. Count words and characters (ignoring extra whitespace).
    3. Compute time with a word-based and a character-based model.
    4. Return the average (rounded to 1 decimal place) + a human-readable string.

    Parameters
    ----------
    text               : input string, may contain [brackets]
    words_per_minute   : speaking speed in words/min (default 150 wpm)
    chars_per_minute   : speaking speed in characters/min (default 750 cpm)
    min_seconds        : floor for very short texts

    Returns
    -------
    (seconds, "X min Y sec")
    """
    # ------------------------------------------------------------------ #
    # 1. Remove [anything inside square brackets] – including the brackets
    # ------------------------------------------------------------------ #
    clean = re.sub(r'\[.*?\]', '', text, flags=re.DOTALL)

    # ------------------------------------------------------------------ #
    # 2. Normalise whitespace (multiple spaces → one, trim)
    # ------------------------------------------------------------------ #
    clean = re.sub(r'\s+', ' ', clean).strip()

    # ------------------------------------------------------------------ #
    # 3. Count words and characters
    # ------------------------------------------------------------------ #

    words = len(clean.split())                # simple split on whitespace
    chars = len(clean.replace(' ', ''))       # characters *without* spaces

    # ------------------------------------------------------------------ #
    # 4. Time estimates
    # ------------------------------------------------------------------ #
    # word-based
    sec_word = (words / words_per_minute) * 60.0

    # character-based (more robust for languages with long compounds)
    sec_char = (chars / chars_per_minute) * 60.0

    # average → most accurate for mixed texts
    seconds = sec_word + sec_char / 2.0

    # round to 1 decimal place
    seconds = round(seconds, 1)

    return seconds


# from one single long string of story
# 1. split by sentences and breaks
# 2. for each sentence add pauses - pause is generated by comma or parts longer than 7 words.

def story_split(story: str) -> List[Any]:
    # split breaks
    pattern = r'(<break time="\d+s"/>)'
    segments = re.split(pattern, story)

    final_segments = []

    for segment in segments:

        if segment.startswith('<break'):
            duration = re.search(r'time="(\d+)s"', segment)
            final_segments.append({
                "type": "break",
                "content": segment,
                "duration": float(duration.group(1)),
                "content_with_pauses": None
            })
        else:
            duration = estimate_speech_time(segment)

            # Content with pauses is sentence with "|".
            # Each "|" suggest that tekst will generate in another scene 

            # 1: Split by dots and commas
            splitted = re.split('[,.]', segment)

            splitted_shorter = []
            for part in splitted:
                final_parts = []
                def split_longer_parts_of_sentence(words: str) -> List[str]:
                    nonlocal final_parts
                    # if the segment is longer than 8 words - split them apart
                    # and if splitted part include more than 8 words - split again recursively
                    words_list = words.split()
                    if len(words_list) < 8:
                        final_parts.append(words.strip())
                    else:
                        middle_index = len(words_list) // 2
                        splitted_first_part = ' '.join(words_list[:middle_index])
                        remaining_part = ' '.join(words_list[middle_index:])
                        split_longer_parts_of_sentence(splitted_first_part)
                        split_longer_parts_of_sentence(remaining_part)
                
                split_longer_parts_of_sentence(part)
                splitted_shorter.append("|".join(final_parts))
            
            content_with_pauses = "|".join(splitted_shorter)
            if content_with_pauses.endswith("|"):
                content_with_pauses = content_with_pauses[:-1]
            
            final_segments.append({
                "type": "text",
                "content": segment,
                "duration": duration, # average speaking cps
                "content_with_pauses": content_with_pauses
            })

    return final_segments


class Scene(BaseModel):
    image_prompt: str
    video_prompt: str
    duration: int  # 3–7 seconds per scene

class SegmentWithScenes(BaseModel):
    content: str
    duration: float  # or int if always integer seconds
    scenes: List[Scene]

class StoryWithScenes(BaseModel):
    story: List[SegmentWithScenes]


def add_scenes_to_story(splitted_story: List[Any]) -> List[Any]:
    # Step 1: Filter and reformat
    filtered_story = [{
        "duration": float(seg["duration"]) + 2,
        "content": seg["content"],
    } for seg in splitted_story if seg.get("type") == "text"]

    total_segments = len(filtered_story)

    def generate_missing_scenes(segment_miss_scenes_indices) -> Dict[int, List[Scene]]:
        if(len(segment_miss_scenes_indices) == 0):
            return
        
        messages = [
            {
                "role": "system",
                "content": "You are an expert film director and visual storyteller."
            },
            {
                "role": "user",
                "content": (
                    "You are an expert film director and visual storyteller specializing in cinematic scene breakdowns "
                    "for AI-generated films. You deeply understand pacing, composition, and emotional continuity. "
                    "Your task is to transform a text-based story into a sequence of visually engaging scenes **for every single segment**.\n\n"

                    "⚠️ CRITICAL ENFORCEMENT RULES:\n"
                    "- Each segment in the input MUST appear in the output.\n"
                    "- Each segment MUST have a non-empty 'scenes' array.\n"
                    "- If a segment is very short, still create at least one valid scene.\n"
                    "- Never skip any segment.\n\n"

                    "Each scene must include:\n"
                    "- 'image_prompt': a vivid, cinematic description of the static frame, optimized for AI image generation.\n"
                    "- 'video_prompt': a concise description of motion (camera moves, character gestures, lighting, or environmental effects).\n"
                    "- 'duration': an integer between 4–7 seconds.\n\n"

                    "The total duration of all scenes in each segment must **cover the segment’s duration** "
                    "and may exceed it by at most 2 seconds.\n\n"

                    "Scene design rules:\n"
                    "- The number of scenes depends on the segment’s duration.\n"
                    "- Each scene = exactly ONE continuous shot or one simple, static visual idea.\n"
                    "- NEVER create montages, photo collages, split-screens, parallel editing, or any scene that consists of multiple images/clips shown at the same time or in quick succession to convey one idea.\n"
                    "- Strictly forbidden: 'montage of X doing Y', 'series of shots showing the passage of time', 'several angles of the same action', 'before-and-after split', 'parallel action in two locations', etc.\n"
                    "- If the script calls for something that would normally be a montage (e.g. training sequence, journey, many days passing, character learning a skill), break it into individual, separate, full-length scenes — each showing only one single moment or one single action.\n"
                    "- Each scene must feel complete on its own; do not rely on rapid cutting or juxtaposition for effect.\n"
                    "- Avoid overly complex choreography, fast cuts, or abstract multi-image compositions.\n"
                    "- Prioritize simplicity: one clear subject, one emotion, one action per scene.\n"
                    "- Maintain smooth pacing, consistent emotional tone within a scene, and strong visual contrast between consecutive scenes.\n\n"

                    "OUTPUT FORMAT (strict JSON):\n"
                    "{\n"
                    "  'story': [\n"
                    "     {\n"
                    "       'content': '...',\n"
                    "       'scenes': [\n"
                    "          {\n"
                    "            'image_prompt': '...',\n"
                    "            'video_prompt': '...',\n"
                    "            'duration': int (4–7)\n"
                    "          }\n"
                    "          ...\n"
                    "        ]\n"
                    "     },\n"
                    "     ...\n"
                    "  ]\n"
                    "}\n\n"


                    f"The story has {len(filtered_story)} segments in total. Therefore, the final output MUST include exactly {len(filtered_story)} segments — each with its own scenes.\n\n"

                    "Story segments:\n"
                    f"{json.dumps(filtered_story, indent=2)}"
                    "\n\n"
                    f"{"I\'ve already filled some sgments" if len(segment_miss_scenes_indices) else "None of the segments have been filled yet."} "
                    f"You need to fill the missing ones (with indices: {segment_miss_scenes_indices.__str__()}). "
                )
            }
        ]
        try:
            response = open_ai_client.chat.completions.create(
                model=ai_model,
                response_model=StoryWithScenes,
                messages=messages,
                temperature=0.7,
            )
            return response.model_dump()["story"]
           
        except Exception as e:
            print(f"Error in scene generation: {e}")
            return {}

    # === Main Loop: Try up to 3 times to fill all segments ===
    max_attempts = 3
    initial_filtered_story = copy.deepcopy(filtered_story)
    segment_miss_scenes_indices = list(range(filtered_story.__len__()))
    for attempt in range(max_attempts):
        filtered_story = generate_missing_scenes(segment_miss_scenes_indices)
        # Check if there are still segments without scenes

        segment_miss_scenes_indices = []
        
        if(initial_filtered_story.__len__() != filtered_story.__len__()):
            for i in range(initial_filtered_story.__len__()):
                if(i >= filtered_story.__len__()):
                    filtered_story.append(initial_filtered_story[i])
        
        for idx, segment in enumerate(filtered_story):
            if not segment.get("scenes") or len(segment["scenes"]) == 0:
                segment_miss_scenes_indices.append(idx)


        print("-----------------------")
        print(json.dumps(filtered_story, indent=2))
        print("-----------------------")
        print(f"Attempt {attempt + 1}: Missing scenes for segments {segment_miss_scenes_indices}")

        if(len(segment_miss_scenes_indices) == 0):
            break

    return filtered_story

def add_scenes_to_story_old(splitted_story: List[Any]) -> List[Any]:
    # TODO
    # Reformat the story for better prompt engineering
    # Changes for the prompt:
    # - remove segments that are type "break"
    # remove video_parts from each segment - this is not needed in the prompt
    # so the final segments should only contain est_duration and content

    # Objective:
    # Add visualization to each segment according to whole story and segment content. The visualisation should be engaging for the viewer to watch.

    # Desired output:
    # Each segment should have added "scenes": [{image_prompts: str, video_prompt duration: int}, ...]
    # More information about scenes:
    # - number of scenes should be determined by:
    # a) est_duration of segment - it should cover full duration of segment with each scene ranging from 3 - 7 seconds
    # b) keeping with content of the segment - f.e when story changes drastically - make sure there are scenes according to words.
    # c) the main priority is to make it engaging for a viewer to watch - making it a good visualisation for the story
    # scene.image_prompt - is a detailed description of scene, which is optimalized description for using AI image generation model. Keep in mind that this is will be the reference image for video_prompt. So the image should already tell the story and the video will just make it live without too many complex moves 
    # scene.video_prompt - this should be information about what is happening with image generated from image_prompt. Avoid too complex action. Stick with camera movement and simple character actions that will not confuse AI.
    

    # remove segments with type = "break"
    filtered_story = [{
        "duration": float(seg["duration"]) + 2,
        "content": seg["content"],
    } for seg in splitted_story if seg.get("type") == "text"]


    messages = messages = [
        {
            "role": "system",
            "content": (
                "You are a visionary Director of Photography and Visual Storyteller known for epic, atmospheric, and hyper-realistic cinematography. "
                "Your visual style is defined by: 'National Geographic meets Ridley Scott'. "
                "You avoid generic, flatly lit scenes. You prioritize mood, lighting, and environmental texture."
            )
        },
        {
            "role": "user",
            "content": (
                "Transform the provided text-based story into a sequence of visually stunning cinematic scenes.\n\n"

                "### 1. VISUAL STYLE BIBLE (STRICT ADHERENCE REQUIRED)\n"
                "All `image_prompt` descriptions must adhere to these three pillars:\n"
                "A. LIGHTING IS KEY: Never describe a scene without describing the light. Use terms like: 'rim-lit', 'volumetric fog', 'firelight glowing on skin', 'moonlight cutting through darkness', 'silhouette against a bright background'.\n"
                "B. ATMOSPHERE & TEXTURE: The air is never empty. It must contain: falling snow, rising dust, visible breath in cold air, swirling mist, embers, or rain. Textures should be vivid (fur, rust, peeling paint, grime).\n"
                "C. SCALE & FRAMING: Avoid boring medium shots. Use either:\n"
                "   - EPIC WIDE SHOTS: Small subject, massive environment (mountains, huge crowds, endless ocean).\n"
                "   - INTENSE CLOSE-UPS: Focus on eyes, hands, or texture, with a blurred background (bokeh).\n\n"

                "### 2. EXAMPLES OF TRANSFORMATION\n"
                "❌ BAD (Boring): 'A man looks sad in the snow.'\n"
                "✅ GOOD (Your Style): 'Extreme close-up profile of a bearded man, his breath visible in the freezing air, illuminated by a harsh blue flare, shallow depth of field.'\n"
                "❌ BAD (Boring): 'A train moves on the tracks.'\n"
                "✅ GOOD (Your Style): 'Wide shot of a rusted train cutting through a dark blizzard, headlights beaming through thick heavy fog, cinematic blue tones.'\n\n"

                "### 3. CRITICAL OUTPUT RULES\n"
                "- Each segment in the input MUST appear in the output.\n"
                "- Each segment MUST have a non-empty 'scenes' array.\n"
                "- If a segment is very short, create at least one valid scene.\n"
                "- 'duration': integer between 4–7 seconds.\n"
                "- The total duration of scenes must cover the segment's duration.\n\n"

                "### 4. OUTPUT FORMAT (Strict JSON)\n"
                "{\n"
                "  'story': [\n"
                "     {\n"
                "       'content': '...',\n"
                "       'scenes': [\n"
                "           {\n"
                "            'image_prompt': 'A vivid description focusing on light, atmosphere, and composition...',\n"
                "            'video_prompt': 'Concise motion description (e.g., Slow push in, rack focus, drone tracking)...',\n"
                "            'duration': 5\n"
                "           }\n"
                "        ]\n"
                "     }\n"
                "  ]\n"
                "}\n\n"

                f"The story has {len(filtered_story)} segments. Generate the JSON output now based on this story:\n"
                f"{json.dumps(filtered_story, indent=2)}"
            )
        }
    ]


    messages_old = [
        {
            "role": "system",
            "content": "You are an expert film director and visual storyteller."
        },
        {
            "role": "user",
            "content": (
                "You are an expert film director and visual storyteller specializing in cinematic scene breakdowns "
                "for AI-generated films. You deeply understand pacing, composition, and emotional continuity. "
                "Your task is to transform a text-based story into a sequence of visually engaging scenes **for every single segment**.\n\n"

                "⚠️ CRITICAL ENFORCEMENT RULES:\n"
                "- Each segment in the input MUST appear in the output.\n"
                "- Each segment MUST have a non-empty 'scenes' array.\n"
                "- If a segment is very short, still create at least one valid scene.\n"
                "- Never skip any segment.\n\n"

                "Each scene must include:\n"
                "- 'image_prompt': a vivid, cinematic description of the static frame, optimized for AI image generation.\n"
                "- 'video_prompt': a concise description of motion (camera moves, character gestures, lighting, or environmental effects).\n"
                "- 'duration': an integer between 4–7 seconds.\n\n"

                "The total duration of all scenes in each segment must **cover the segment’s duration** "
                "and may exceed it by at most 2 seconds.\n\n"

                "Scene design rules:\n"
                "- The number of scenes depends on the segment’s duration.\n"
                "- Each scene should align with a meaningful change in the story — a new action, mood, or visual element.\n"
                "- Avoid overly complex choreography or abstract imagery.\n"
                "- If a montage or quick transition fits naturally, break it into several shorter scenes instead of one.\n"
                "- Maintain smooth pacing, emotional tone, and visual diversity.\n\n"

                "OUTPUT FORMAT (strict JSON):\n"
                "{\n"
                "  'story': [\n"
                "     {\n"
                "       'content': '...',\n"
                "       'scenes': [\n"
                "          {\n"
                "            'image_prompt': '...',\n"
                "            'video_prompt': '...',\n"
                "            'duration': int (4–7)\n"
                "          }\n"
                "          ...\n"
                "        ]\n"
                "     },\n"
                "     ...\n"
                "  ]\n"
                "}\n\n"


                f"The story has {len(filtered_story)} segments in total. Therefore, the final output MUST include exactly {len(filtered_story)} segments — each with its own scenes.\n\n"

                "Story segments:\n"
                f"{json.dumps(filtered_story, indent=2)}"
            )
        }
    ]

    response = open_ai_client.chat.completions.create(
        model=ai_model,
        response_model=StoryWithScenes,
        messages=messages
    )

    return response

def prepare_story_for_db(story_with_scenes, splitted_story):
    # story_with_scenes containst segments with: est_duration, content and scenes
    # splitted_story contains est_duration, content, type
    # join them by the same content
    segments_with_scenes_len = len(story_with_scenes)
    i = 0
    for segment in splitted_story:
        if segment["type"] == "break":
            continue
        else:
            if segments_with_scenes_len <= i:
                break
            else:
                segment["scenes"] = story_with_scenes[i].get("scenes", [])
                i += 1
    try:
        print("------------JOINED------------")
        print(json.dumps(splitted_story, indent=2))
        print("-------------------------------")
    except:
        print("not working")

    # Step 1: Add start_time to each segment (sum of previous est_durations)
    current_time = 0
    for segment in splitted_story:
        segment['start_time'] = current_time
        current_time += float(segment['duration'])

    # Step 2: Create voiceovers list
    voiceovers = []
    for segment in splitted_story:
        if segment["type"] == 'text':
            voiceovers.append({
                'content': segment['content'],
                'content_with_pauses': segment['content_with_pauses'],
                'duration': segment['duration'],
                'start_time': segment['start_time']
            })

    # Step 3: Create scenes list with calculated start times
    scenes = []
    for segment in splitted_story:
        segment_start_time = segment['start_time']
        current_scene_time = 0
        for scene in segment.get('scenes', []):
            start_time = float(segment_start_time) + float(current_scene_time)
            scenes.append({
                **scene,  # Copy all existing scene data
                'start_time': start_time
            })
            current_scene_time += float(scene.get('duration', 0))

    return {
        'voiceovers': voiceovers,
        'scenes': scenes,
    }


class PersistantCharacter(BaseModel):
    name: str
    image_prompt: str
    scenes: List[int] 

class ChangedScene(BaseModel):
    scene_index: int
    new_image_prompt: str

class CharacterUpdate(BaseModel):
    persistant_characters: List[PersistantCharacter]
    changed_scenes: List[ChangedScene]


def get_persistant_characters(scenes, gathered_data):
    
    print("----scenes----")
    print(json.dumps(scenes, indent=2))
    print("----gathered data----")
    print(json.dumps(gathered_data, indent=2))

    messages = [
    {
        "role": "system",
        "content": (
            "You are a JSON-only extractor assistant. "
            "Your job is to analyze given scene descriptions and contextual data about characters, "
            "then produce a single structured JSON output that identifies persistent characters and modified scenes. "
            "Always output only valid JSON, with no explanations or extra text."
        )
    },
    {
        "role": "user",
        "content": (
            "Given two inputs—`scenes` (a list of image-description prompts, where each element is a string describing what is in the scene) "
            "and `gathered_data` (context about the topic and characters)—produce exactly one JSON object matching the CharacterUpdate schema below and nothing else. "
            "Use 0-based indexing for scene indices. Do NOT include any explanatory text, code fences, or extra fields. "
            "If a field is empty, return an empty list for that field.\n\n"
            "Output schema (exact keys & types):\n"
            "{\n"
            '  \"persistant_characters\": [\n'
            "    { \"name\": string, \"image_prompt\": string, \"scenes\": [int, ...] }\n"
            "  ],\n"
            '  \"changed_scenes\": [\n'
            "    { \"scene_index\": int, \"new_image_prompt\": string }\n"
            "  ]\n"
            "}\n\n"

            "STEP 1 – Coreference and alias mapping:"
            "Identify all aliases, nicknames, pronouns, or descriptive mentions that refer to the same named individual."
            "Example:"
            "- gathered_data says “Main character: Władysław Mazurkiewicz”"
            "- scene descriptions include phrases like “the gentleman,” “the charming man,” “the killer,” or “he”"
            "⟶ Treat ALL of these as referring to the same person: “Władysław Mazurkiewicz”."
            "You must apply this mapping before deciding which characters are persistent."
            "STEP 2 – Persistency analysis:"
            "After alias mapping, treat any scene that contains any of those aliases, pronouns, or name mentions as featuring that person."

            "Rules & behavior (apply these exactly):\n"
            "1) Identify persistent characters using both scene descriptions AND gathered_data context. A character is considered persistent if:\n"
            "   - They appear (explicitly by name OR implicitly through consistent description) across multiple scenes, OR\n"
            "   - gathered_data identifies them as a main or central figure (protagonist, historical subject, narrator, etc.), even if some scenes only describe them indirectly (e.g. 'the gentleman', 'the killer', 'he', 'the woman', etc.).\n"
            "2) You MUST infer when recurring descriptions clearly refer to the same individual, even if the name is omitted. Example: if gathered_data says the main character is 'Władysław Mazurkiewicz', and multiple scenes describe 'a gentleman', 'a charming man', or 'Mazurkiewicz', treat all those as referring to him.\n"
            "3) For each persistent character:\n"
            "   - name: use the explicit or inferred name.\n"
            "   - image_prompt: construct a full-body reference image description following the Image Prompt Template below.\n"
            "   - scenes: list all 0-based indices where this person appears, whether explicit or inferred.\n"
            "4) Image Prompt Template (use this structure when you create `image_prompt` for a referenceable person):\n"
            "   - If the character is a real person or there is a good reference image available online, the prompt MUST include the phrase: 'Reference image contains face of the character' and must describe a full-person reference photograph on a white background. "
            "The prompt must be suitable for generating a reference image (full-body, neutral pose, clothing suitable for character, clear age/build/hair/facial features). Example structure:\n"
            "     'Reference image: <PERSON NAME>\\nReference image contains face of the character\\nGeneral description: <build, age, sex, height/approx, distinguishing features>\\nClothing: <suitable clothing description for the character given gathered_data>\\nPose & framing: full-body, neutral standing pose, 3/4 view, visible hands and feet, head-to-toe in frame\\nBackground: white background\\nAdditional notes: <hair color/length, facial hair, ethnicity cues if relevant, expression neutral/serious/etc>'\n"
            "   - If the character is fictional or no real reference exists, create an equally detailed full-body description on a white background (same framing/pose requirements). Use concrete visual details so generated images can be used as references.\n"
            "5) If the same character appears with significantly different ages or appearances across scenes (example: 16yo vs 40yo), create separate PersistantCharacter entries per distinct consistent appearance if each appearance occurs in multiple scenes. "
            "If a distinct appearance occurs only once (e.g., a single flashback with a younger version that appears in only one scene), DO NOT create a PersistantCharacter for that single-appearance variant — instead add a ChangedScene entry that updates that single scene's image prompt to reference the main reference plus a note like 'younger version'.\n"
            "6) For every scene that should be updated to explicitly use the reference image, add a ChangedScene entry with `scene_index` and `new_image_prompt` where you modify the original scene prompt so the character's name or description is replaced or appended with: "
            "'Reference image of <NAME>'. If it is a different appearance variant, include that explicitly (e.g. 'Reference image of <NAME> — younger version (16 yrs)'). The `new_image_prompt` should still be a complete prompt describing the whole scene, but with the character reference inserted so image generation will use the reference for that character.\n"
            "7) If no persistent characters are found, return 'persistant_characters: []' and only supply 'changed_scenes' if you adjusted any single scenes for clarity; otherwise 'changed_scenes: []'.\n"
            "8) Use 0-based indices for all `scene_index` and `scenes` lists.\n"
            "9) Be logical but decisive — if gathered_data makes a person central, treat them as persistent even if not named in every scene.\n"
            "10) Output ONLY the JSON object, with no explanations or markdown.\n\n"
            "Inputs:\n"
            f"SCENES: \n{json.dumps(scenes)}\n\n"
            f"GATHERED_DATA: \n{json.dumps(gathered_data)}\n\n"
            "Example outputs:\n\n"
            "Example 1 (same character appears in multiple scenes):\n"
            "{\n"
            "  \"persistant_characters\": [\n"
            "    {\n"
            "      \"name\": \"Marek Kowalski\",\n"
            "      \"image_prompt\": \"Reference image: Marek Kowalski\\nReference image contains face of the character\\nGeneral description: skinny, 28-year-old Polish male, 180 cm, short dark hair, light stubble\\nClothing: worn leather jacket, dark jeans, sturdy boots (suitable for an everyman mechanic)\\nPose & framing: full-body, neutral standing pose, 3/4 view, head-to-toe in frame\\nBackground: white background\",\n"
            "      \"scenes\": [0, 2]\n"
            "    }\n"
            "  ],\n"
            "  \"changed_scenes\": [\n"
            "    {\n"
            "      \"scene_index\": 0,\n"
            "      \"new_image_prompt\": \"Street at dusk, Marek Kowalski (Reference image of Marek Kowalski) leaning on a red motorcycle, wet pavement, neon reflections, cinematic lighting\"\n"
            "    },\n"
            "    {\n"
            "      \"scene_index\": 2,\n"
            "      \"new_image_prompt\": \"Interior garage, Marek Kowalski (Reference image of Marek Kowalski) working on an engine, scattered tools, warm tungsten light\"\n"
            "    }\n"
            "  ]\n"
            "}\n\n"
            "Example 2 (no persistent characters):\n"
            "{\n"
            "  \"persistant_characters\": [],\n"
            "  \"changed_scenes\": []\n"
            "}\n\n"
            "Now analyze the provided inputs and return only the JSON CharacterUpdate object."
        )
    }
    ]
    response = open_ai_client.chat.completions.create(
        model=ai_model,
        response_model=CharacterUpdate,
        messages=messages
    )

    return response.model_dump()


def add_character_changes(story, character_updates):
    story["characters"] = character_updates["persistant_characters"]
    # add character to given scenes
    for character in character_updates["persistant_characters"]:
        for scene_index in character["scenes"]:
            print(scene_index)
            print(len(story["scenes"]))
            print(story["scenes"][scene_index])
            if not "characters" in story["scenes"][scene_index]:
                story["scenes"][scene_index]["characters"] = []

            story["scenes"][scene_index]["characters"].append(character["name"])
    # correct image_prompt
    for changed_scene in character_updates["changed_scenes"]:
        story["scenes"][changed_scene["scene_index"]]["image_prompt"] = changed_scene["new_image_prompt"]

    
