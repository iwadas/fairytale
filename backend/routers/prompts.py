from math import floor
import os  # Added missing import
from openai import OpenAI
import instructor
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json  # Added for debug logging
import re


load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
open_ai_client = instructor.from_openai(OpenAI(api_key=OPENAI_API_KEY))


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
        model="gpt-4o-mini",
        response_model=GatheredStoryData,
        messages=messages
    )

    # Debug: Log the AI response
    print("DEBUG: gather_story_data response:")
    print(json.dumps(response.model_dump(), indent=2))

    return response

class Story(BaseModel):
    script: str

def generate_story(topic: str, word_limit: int, story_data: GatheredStoryData) -> Story:
    messages = [
        {
            "role": "system",
            "content": (
                "You are an excellent storyteller who writes engaging, voice-ready narratives for video scripts. "
                "Your main goal is to make the story sound like it's being told out loud by a passionate narrator. "
                "You use emotional delivery and natural pacing to make the listener *feel* the story, not just hear it."
            )
        },
        {
            "role": "user",
            "content": (
                f"Create a captivating story about '{topic}'.\n\n"
                f"Base it entirely on the following data:\n{story_data.gathered_data}\n\n"
                f"Guidelines:\n"
                f"- Vocabulary: 7th-grade reading level.\n"
                f"- Style: Conversational, suspenseful, and easy to follow.\n"
                f"- Structure: Intro hook → Main events → Reflection.\n"
                f"- Length: Around {word_limit} words (not counting tags).\n\n"
                f"🎭 **Emotion and pacing:**\n"
                f"Use the following tags to make the story sound like spoken performance — not too often, but enough to make it expressive.\n"
                f"- **SSML breaks:** Use `<break time=\"1s\"/>` or `<break time=\"2s\"/>` where a narrator would naturally pause — for tension, reflection, or transition.\n"
                f"- **Emotion and tone tags:** You can use tags like [happy], [sad], [excited], [fearful], [curious], [quietly], [whisper], [shout], etc.\n"
                f"  Example: [whisper][curious]But what happened next?\n"
                f"- **Use them meaningfully:** Include these tags only when they enhance the listener's emotional engagement.\n"
                f"  Think about how a storyteller would speak — add tags for emotional or dramatic parts, "
                f"but avoid overuse (around 1-2 emotion or pacing tags per short paragraph is ideal).\n\n"
                f"Output only the final story string, ready for text-to-speech."
            )
        }
    ]
    response = open_ai_client.chat.completions.create(
        model="gpt-4o-mini",
        response_model=Story,
        messages=messages
    )

    # Debug: Log the AI response
    print("DEBUG: generate_voiceovers response:")
    print(json.dumps(response.model_dump(), indent=2))

    return response

def story_split(story: str) -> List[Any]:
    # First, split by break tags to preserve them as separate elements
    pattern = r'(<break time="\d+s"/>)'
    parts = re.split(pattern, story)
    
    # if segment contains '.', split by dots
    # if the splitted part is empty - remove it
    def split_by_dots(segment: str) -> List[Any]:
        if '.' in segment:
            sub_parts = [part.strip() for part in segment.split('.') if part.strip()]
            # Remove the extra dot added to the last part if it was originally empty
            if sub_parts and sub_parts[-1] == '.':
                sub_parts.pop()
            return sub_parts
        else:
            return [segment.strip()] if segment.strip() else []

    final_parts = []
    for part in parts:
        split_parts = split_by_dots(part)
        final_parts.extend(split_parts)

    final_parts = finalize_voiceover_segments(final_parts)
    return final_parts


def finalize_voiceover_segments(segments: list[str]) -> list[Dict[str, Any]]:
    finalized_segments = []
    # This should split the segments to be 4 - 7 words long instead of one long segment
    def split_video_segment(segment: str) -> List[str]:
 
        def split_by_commas(words: str) -> List[str]:
            segments = []
            current_segment = []
            for word in words.split():
                current_segment.append(word)
                if word.endswith(','):
                    segments.append(' '.join(current_segment).strip())
                    current_segment = []
            if current_segment:
                segments.append(' '.join(current_segment).strip())
            return segments
        split_by_commas(segment)
        final_parts = []
        def shorten_segments(words: str) -> List[str]:
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
                shorten_segments(splitted_first_part)
                shorten_segments(remaining_part)

        shorten_segments(segment)

        def add_duration_for_parts(segment) -> List[str]:
            # TODO
            # Get percentage of duration for each part based on number of characters - and give approx duration
            # Sum of all est_duration of video_parts should be equal to est_duration of the whole segment
            total_chars = len(segment.content)
            for part in segment.video_parts:
                part_duration = floor((len(part) / total_chars) * segment.est_duration)
        
            # add time to shortest part to make sum equal to est_duration
            total_duration = segment.est_duration
            current_sum = sum(floor((len(part) / total_chars) * segment.est_duration) for part in segment.video_parts)
            duration_difference = total_duration - current_sum

            parts_sorted_by_length = sorted(segment.video_parts, key=lambda x: len(x))

            # Split the duration_difference across the parts, according to their length
            # So the shortest parts should get the most extra time and longest parts the least - this should be
            for i in range(abs(duration_difference)):
                if duration_difference > 0:
                    parts_sorted_by_length[i % len(parts_sorted_by_length)].duration += 1
                else:
                    parts_sorted_by_length[i % len(parts_sorted_by_length)].duration -= 1
            pass
        
        return final_parts
    

    for segment in segments:
        if segment.startswith('<break'):
            duration = re.search(r'time="(\d+)s"', segment)
            finalized_segments.append({
                "type": "break",
                "content": segment,
                "est_duration": duration.group(1),
            })
        else:
            # avertage characters per second is 8.5
            est_duration = len(segment) / 8.5
            finalized_segments.append({
                "type": "text", 
                "content": segment, 
                "est_duration": round(est_duration),
                "video_parts": split_video_segment(segment)
            })
            
    return finalized_segments

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
        "est_duration": seg.est_duration,
        "content": seg.content,
    } for seg in splitted_story if seg.get("type") == "text"]
    
    filtered_story = json.dumps(filtered_story, ensure_ascii=False, indent=2)

    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert film director and visual storyteller specializing in creating cinematic scene breakdowns "
                "for AI-generated films. You deeply understand pacing, composition, and visual engagement. "
                "Your task is to transform a text-based story into a sequence of visually engaging scenes for each segment. "
                "Each scene will have a detailed 'image_prompt' describing the visual frame, and a simple 'video_prompt' "
                "that defines what happens in motion (camera movement, small character actions, environmental changes). "
                "The result should be a JSON structure matching the 'Story' schema: "
                "Story -> List[SegmentWithScenes(content: str, scenes: List[dict(image_prompt:str, video_prompt:str, duration:int)])]. "
                "Focus on maintaining narrative flow, emotional tone, and visual diversity. "
                "Avoid repetitive or overly complex camera actions. "
                "Scenes should be visually rich, consistent with the tone of the story, and make viewers feel immersed. "
                "Important: The total sum of scene durations for each segment **must not exceed the segment’s duration by more than 2 seconds**."
            )
        },
        {
            "role": "user",
            "content": (
                "Below is the story split into segments. Each segment contains the estimated duration and its text content. "
                "Your goal is to enrich each segment with 'scenes', covering the entire duration. "
                "Each scene should last between 3 and 7 seconds, and the **total duration of all scenes in a segment should be ≤ segment duration + 2 seconds**. "
                "Use these rules:\n\n"
                "- The number of scenes depends on the segment’s estimated duration.\n"
                "- Each scene must align with narrative changes or important visual details in the text.\n"
                "- For each scene:\n"
                "  * 'image_prompt' should describe the static frame in rich cinematic detail, optimized for AI image generation.\n"
                "  * 'video_prompt' should describe how the scene moves slightly — camera pans, zooms, slow character actions, weather shifts.\n"
                "  * Avoid complex multi-character choreography, fast transitions, or abstract visual concepts.\n\n"
                "Output format:\n"
                "{\n"
                "  'story': [\n"
                "     {\n"
                "       'content': '...',\n"
                "       'scenes': [\n"
                "          {\n"
                "            'image_prompt': '...',\n"
                "            'video_prompt': '...',\n"
                "            'duration': int (3-7 seconds)\n"
                "          }\n"
                "        ]\n"
                "     }\n"
                "  ]\n"
                "}\n\n"
                "Story segments:\n"
                f"{filtered_story}"
            )
        }
    ]

    print("message:")
    print(json.dumps(messages))

    response = open_ai_client.chat.completions.create(
        model="gpt-4o-mini",
        response_model=StoryWithScenes,
        messages=messages
    )

    

    # DEBUG PRINT OF RESPONSE
    print("response:")
    print(json.dumps(response.model_dump(), indent=2))



    return response

def prepare_story_for_db(story_with_scenes, splitted_story):
    # story_with_scenes containst segments with: est_duration, content and scenes
    # splitted_story contains est_duration, content, type
    # join them by the same content
    for segment in splitted_story:
        if segment['type'] == 'text':
            for scene_segment in story_with_scenes:
                if scene_segment['content'] == segment['content']:
                    segment['scenes'] = scene_segment.get('scenes', [])
                    break

    # Step 1: Add start_time to each segment (sum of previous est_durations)
    current_time = 0
    for segment in splitted_story:
        segment['start_time'] = current_time
        current_time += float(segment['est_duration'])

    # Step 2: Create voiceovers list
    voiceovers = [
        {
            'content': segment['content'],
            'video_parts': segment.get('video_parts', []),
            'est_duration': segment['est_duration'],
            'start_time': segment['start_time']
        }
        for segment in splitted_story
    ]

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
    

