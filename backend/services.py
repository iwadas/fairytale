import time
import mimetypes
import uuid
import json
import os
import requests
from pathlib import Path
from PIL import Image
import base64
from io import BytesIO

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from mutagen.mp3 import MP3
from moviepy import VideoFileClip, CompositeAudioClip, AudioFileClip, AudioClip


from fastapi import HTTPException

from google import genai  
from google.genai import types
from elevenlabs import ElevenLabs, VoiceSettings
from dotenv import load_dotenv
from pydub import AudioSegment

load_dotenv()
GENAI_API_KEY = os.getenv("GENAI_API_KEY")
RUNWARE_API_KEY = os.getenv("RUNWARE_API_KEY")
ELEVEN_LABS_API_KEY = os.getenv("ELEVEN_LABS_API_KEY")

google_client = genai.Client(api_key=GENAI_API_KEY)
eleven_labs_client = ElevenLabs(api_key=ELEVEN_LABS_API_KEY)


fps = 24
width_image = 1024
height_image = 1024
width = 960
height = 960

def create_typing_video(text, duration=10, output_filename='static/videos/scenes/typing_effect.mp4'):
    """
    Generate a typing effect video on a black screen with specified dimensions, with a single typing sound subclipped to match the typing duration, starting after initial_delay.

    Args:
    - text (str): The text to type.
    - duration (int/float): Total video duration in seconds.
    - output_filename (str): Output file name (MP4 or GIF).
    """
    # Setup
    chars_per_second = 10
    total_frames = int(duration * fps)
    initial_delay = 1.5
    typing_sound_path = 'static/default/sounds/typing_sound.mp3'

    lines = text.split('\n')
    num_lines = len(lines)
    chars = list(text.replace('\n', ''))  # Flatten text for typing, ignoring newlines
    num_chars = len(chars)
    if num_chars == 0:
        print("Text is empty. No video generated.")
        return
    
    # Calculate frames and typing duration
    frames_per_char = fps / chars_per_second  # Frames per character
    char_duration = 1 / chars_per_second  # Duration per character in seconds
    typing_duration = num_chars * char_duration  # Total duration of actual typing
    total_frames = int(duration * fps)
    
    # Figure setup: black background, convert pixel dimensions to inches
    dpi = 100
    fig_width = width / dpi
    fig_height = height / dpi
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), facecolor='black', dpi=dpi)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_facecolor('black')
    ax.axis('off')
    
    # Text setup: create text objects for each line
    font_size = height / (30 * max(1, num_lines * 0.5))  # Scale font with number of lines
    line_spacing = 0.1  # Small gap between lines (in axes coordinates)
    base_y = 0.1  # Bottom anchor (10% from bottom of screen)
    text_objects = []
    for i, line in enumerate(lines):
        y_pos = base_y + (num_lines - 1 - i) * line_spacing  # Stack lines upward
        text_obj = ax.text(0.5, y_pos, '', ha='center', va='center', 
                          fontsize=font_size, color='white', transform=ax.transAxes)
        text_objects.append((text_obj, line))
    
    def update(frame):
        # Determine how many characters to show
        char_index = -1 if frame < initial_delay * fps else min(int((frame - initial_delay * fps) / frames_per_char), num_chars - 1)
        
        # Rebuild lines with typed characters
        char_pos = 0
        for text_obj, line in text_objects:
            line_len = len(line)
            if char_pos <= char_index < char_pos + line_len:
                text_obj.set_text(line[:char_index - char_pos + 1])
            elif char_index >= char_pos + line_len:
                text_obj.set_text(line)
            else:
                text_obj.set_text('')
            char_pos += line_len
        
        return [obj for obj, _ in text_objects]
    
    # Create animation
    ani = FuncAnimation(fig, update, frames=total_frames, interval=1000 / fps, 
                        blit=True, repeat=False)
    
    temp_video_file = 'temp_typing_video.mp4'
    writer = 'ffmpeg'
    print("Generating temporary video with FFmpeg writer.")
    ani.save(temp_video_file, writer=writer, fps=fps)
    plt.close(fig)
    
    # Load the temporary video using MoviePy
    video = VideoFileClip(temp_video_file)
    
    # Load typing sound and subclip to match total typing duration
    try:
        typing_sound = AudioFileClip(typing_sound_path)
        # Subclip the typing sound to match the total typing duration
        typing_sound = typing_sound.with_duration(min(typing_sound.duration, typing_duration))
        # Create a silent audio clip for the initial delay
        silence = AudioClip(lambda t: 0, duration=initial_delay)
        # Combine silence and typing sound, with typing sound starting after initial_delay
        final_audio = CompositeAudioClip([silence, typing_sound.with_start(initial_delay - 0.2)])
    except Exception as e:
        print(f"Error loading typing sound: {e}")
        video.write_videofile(output_filename)
        video.close()
        return
    
    # Add the single typing sound to the video
    video = video.with_audio(final_audio)
    
    # Save final video
    video.write_videofile(output_filename)
    video.close()
    typing_sound.close()
    silence.close()  # Close the silent audio clip
    final_audio.close()  # Close the composite audio clip
    print(f"Video with typing sound saved as {output_filename}")
    return output_filename

def pil_to_part(path: str, mime="image/png") -> types.Part:
    with open(path, "rb") as f:
        data = f.read()
    return types.Part(
        inline_data=types.Blob(
            mime_type=mime,
            data=base64.b64encode(data).decode("utf-8"),
        )
    )

def file_to_part(file_obj, mime="image/png") -> types.Part:
    # Case 1: FastAPI UploadFile
    if hasattr(file_obj, "file"):
        data = file_obj.file.read()
    # Case 2: Regular file handle from open()
    elif hasattr(file_obj, "read"):
        data = file_obj.read()
    # Case 3: Just a path string
    elif isinstance(file_obj, (str, Path)):
        with open(file_obj, "rb") as f:
            data = f.read()
    else:
        raise TypeError(f"Unsupported file type: {type(file_obj)}")

    return types.Part(
        inline_data=types.Blob(
            mime_type=mime,
            data=base64.b64encode(data).decode("utf-8"),
        )
    )

def parse_skrypt(skrypt):
    scenes = []
    lines = skrypt.split('\n')
    current_scene = {}
    for line in lines:
        if line.strip().startswith('Scene'):
            if current_scene:
                scenes.append(current_scene)
            current_scene = {"start_img_desc": "", "end_img_desc": "", "voiceover": ""}
        elif 'Start img:' in line:
            current_scene['start_img_desc'] = line.split('Start img: ')[1] if 'Start img: ' in line else ""
        elif 'End img:' in line:
            current_scene['end_img_desc'] = line.split('End img: ')[1] if 'End img: ' in line else ""
        elif 'Voiceover:' in line:
            current_scene['voiceover'] = line.split('Voiceover: ')[1] if 'Voiceover: ' in line else ""
    if current_scene:
        scenes.append(current_scene)
    # Fallback: If parsing fails, create dummy scenes
    if not scenes:
        scenes = [{"start_img_desc": "Placeholder start", "end_img_desc": "Placeholder end", "voiceover": "Placeholder voiceover"}]
    return scenes


def alignment_to_words_with_emotion_tags(characters, character_start_times_seconds):
    """
    Converts character-level alignment to word-level with emotion tags preserved.
    
    Args:
        characters: list of individual characters (including [ , ], spaces, punctuation)
        character_start_times_seconds: list of start times for each character
        character_end_times_seconds: list of end times for each character
    
    Returns:
        List of dicts: [{'word': str, 'time': float}, ...]
        - Emotion tags like [curious] are kept as full words with their start time
        - Regular words are grouped by spaces
    """
    print('iterating')

    if len(characters) != len(character_start_times_seconds):
        print("not same lengths")
        raise ValueError("All input lists must have the same length")

    print('iterating')

    result = []
    i = 0
    n = len(characters)

    while i < n:
        char = characters[i]
        start_time = character_start_times_seconds[i]

        # Case 1: Emotion tag like [curious]
        if char == '[':
            # Find closing ]
            tag = ''
            tag_start = start_time
            j = i
            while j < n and characters[j] != ']':
                tag += characters[j]
                j += 1
            if j < n:
                tag += ']'
                # Use the start time of the '[' as the tag time
                result.append({'word': tag, 'time': tag_start})
                i = j + 1  # skip past ]
            else:
                # No closing ], treat as regular char
                result.append({'word': char, 'time': start_time})
                i += 1
            continue

        print('removed emotion tags')

        # Case 2: Regular word (accumulate until space or punctuation that breaks word)
        word = ''
        word_start = start_time
        while i < n:
            char = characters[i]
            if char == ' ' or char in ',."\'!?;:' or char == '[':
                if word:  # only add if we have accumulated a word
                    result.append({'word': word, 'time': word_start})
                    word = ''
                if char != ' ':  # keep punctuation as separate if needed, or skip spaces
                    result.append({'word': char, 'time': character_start_times_seconds[i]})
                i += 1
                break
            else:
                if not word:
                    word_start = character_start_times_seconds[i]
                word += char
                i += 1
        else:
            # End of input
            if word:
                result.append({'word': word, 'time': word_start})

    print("got result")
    print(result)
    return result


def generate_speech(text: str, filename="voiceover", directory="static/voiceovers/", voice_id="Cz0K1kOv9tD8l0b5Qu53"):
    response = eleven_labs_client.text_to_speech.convert_with_timestamps(
        text=text,
        voice_id=voice_id,  # Valid voice ID (Brian)
        model_id="eleven_v3",  # Correct model ID
        voice_settings = VoiceSettings(
            stability=0.5,  # For emotional expressiveness
            similarity_boost=0.8,
            style_exaggeration=0.6
        )
    )

    # Make sure the directory exists
    os.makedirs(directory, exist_ok=True)

    # Build full file path
    output_path = os.path.join(directory, f"{filename}.mp3")

    # Decode base64 audio and write to file
    try:
        audio_bytes = base64.b64decode(response.audio_base_64)  # Decode base64 to bytes
        with open(output_path, "wb") as f:
            f.write(audio_bytes)  # Write decoded bytes to file
        print("Wrote audio using response.audio_base_64")
    except AttributeError as e:
        raise AttributeError(f"Could not access audio_base_64. Available attributes: {dir(response)}") from e
    except base64.binascii.Error as e:
        raise ValueError(f"Failed to decode base64 audio: {str(e)}")

    # Print word-level timestamps using alignment
    print("Word-level timestamps:")
    timestamps = []
    try:
        # Debug: Print structure of alignment to confirm format
        print("Alignment structure:", response.alignment)
        timestamps = alignment_to_words_with_emotion_tags(response.alignment.characters, response.alignment.character_start_times_seconds)
    except AttributeError as e:
        print('error in alignment')
        pass

    # Get duration of the generated audio
    try:
        audio_file = MP3(output_path)
        duration = audio_file.info.length  # Duration in seconds
    except Exception as e:
        raise Exception(f"Failed to read MP3 duration: {str(e)}")

    return output_path, duration, timestamps

async def generate_image(directory="static/images/default/", filename="image", prompt="Generate", content_images: dict = {}, lowkey = True):
    if lowkey:
        return await generate_image_runware(directory, filename, prompt, content_images)
    else:
        return generate_image_banana(directory, filename, prompt, content_images)


async def generate_image_runware(directory="static/images/default/", filename="image", prompt="Generate", content_images: dict = {}):
    os.makedirs(directory, exist_ok=True)
    output_path = os.path.join(directory, f"{filename}.png")

    url = "https://api.runware.ai/v1/image/generate"
    headers = {
        "Authorization": f"Bearer {RUNWARE_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "taskType": "imageInference",
        "taskUUID": str(uuid.uuid4()),
        "model": "runware:106@1",  # Adjust model as needed for Runware image generation
        "positivePrompt": prompt,
        "outputType": "URL",
        "outputFormat": "png",
        "height": height_image,  # Default height, adjust as needed
        "width": width_image,   # Default width, adjust as needed
        "deliveryMethod": "async",
        "strenth": 0.5,
        "steps": 50,
    }

    # Handle content images if provided
    if content_images:
        for name, upload_file in content_images.items():
            img_bytes = await upload_file.read()
            mime_type, _ = mimetypes.guess_type(upload_file.filename)

            if mime_type is None:
                ext = os.path.splitext(upload_file.filename)[1].lower()
                if ext == '.png':
                    mime_type = 'image/png'
                elif ext in ('.jpg', '.jpeg'):
                    mime_type = 'image/jpeg'
                elif ext == '.webp':
                    mime_type = 'image/webp'
                else:
                    raise ValueError(f"Unsupported image extension: {ext}")

            if not mime_type.startswith('image/') or mime_type.split('/')[-1] not in ['png', 'jpeg', 'webp']:
                raise ValueError(f"Unsupported image MIME type: {mime_type}")

            # Encode the image in Base64 data URI format
            image_data_uri = f"data:{mime_type};base64,{base64.b64encode(img_bytes).decode('utf-8')}"
            payload["seedImage"] = image_data_uri
            print(f"Including image {name} as seedImage in payload")
        # Wrap in array as required by Runware

    request_body = [payload]

    print("Request payload:", json.dumps(request_body, indent=2))

    # Send request to Runware API
    response = requests.post(url, headers=headers, json=request_body, timeout=120)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Runware API error: {response.text}")

    result = response.json()
    print("Runware API response:", json.dumps(result, indent=2))
    if "errors" in result and result["errors"]:
        raise HTTPException(status_code=500, detail=f"Runware API errors: {result['errors']}")
    if "data" not in result or not result["data"]:
        raise HTTPException(status_code=500, detail=f"Unexpected Runware response: {result}")

    # Check if image URL is immediately available or requires polling
    if "url" not in result["data"][0]:
        print("Task is pending, polling for result...")
        task_uuid = result["data"][0]["taskUUID"]
        print(f"Extracted task UUID: {task_uuid}")
        poll_url = "https://api.runware.ai/v1/task"
        max_attempts = 15
        poll_interval = 5

        poll_headers = {
            "Authorization": f"Bearer {RUNWARE_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        poll_payload = [{
            "taskUUID": task_uuid,
            "taskType": "getResponse",
        }]

        for attempt in range(max_attempts):
            time.sleep(poll_interval)
            try:
                print(f"Polling attempt {attempt + 1}/{max_attempts} for task UUID: {task_uuid}")
                poll_response = requests.post(poll_url, headers=poll_headers, json=poll_payload, timeout=30)
                poll_response.raise_for_status()
                poll_result = poll_response.json()
                print(f"Polling response: {json.dumps(poll_result, indent=2)}")

                if "data" in poll_result and poll_result["data"]:
                    if poll_result["data"][0].get("status") == "success":
                        image_url = poll_result["data"][0].get("imageURL")
                        if not image_url:
                            raise ValueError("Task completed but no image URL found")
                        print(f"Image URL retrieved: {image_url}")
                        break
                    elif poll_result["data"][0].get("taskStatus") == "FAILED":
                        raise HTTPException(status_code=500, detail=f"Image generation failed: {poll_result['data'][0].get('error', 'Unknown error')}")
            except requests.exceptions.HTTPError as e:
                print(f"Polling attempt {attempt + 1} failed with HTTP error: {e}")
                print(f"Response body: {poll_response.text}")
                if attempt == max_attempts - 1:
                    raise HTTPException(status_code=500, detail=f"Polling failed after {max_attempts} attempts: {e}")
            except requests.exceptions.RequestException as e:
                print(f"Polling attempt {attempt + 1} failed: {e}")
                if attempt == max_attempts - 1:
                    raise HTTPException(status_code=500, detail=f"Polling failed after {max_attempts} attempts: {e}")
        else:
            raise HTTPException(status_code=500, detail=f"Image generation timed out after {max_attempts * poll_interval} seconds")
    else:
        image_url = result["data"][0]["url"]

    # Download image from URL to local storage
    r = requests.get(image_url, stream=True, timeout=300)
    r.raise_for_status()
    image = Image.open(BytesIO(r.content))
    
    # Save the image
    if os.path.exists(output_path):
        try:
            os.remove(output_path)
            print(f"Removed existing file: {output_path}")
        except OSError as e:
            print(f"Error removing existing file {output_path}: {e}")
            raise HTTPException(status_code=500, detail=f"Error removing existing file: {e}")

    try:
        image.save(output_path, format="PNG")
        print(f"Saved image to: {output_path}")
    except Exception as e:
        print(f"Error saving image to {output_path}: {e}")
        raise HTTPException(status_code=500, detail=f"Error saving image: {e}")

    return output_path

def generate_image_banana(directory="static/images/default/", filename="image", prompt="Generate", content_images: dict = {}):
    contents = []
    for name, upload_file  in content_images.items():
        contents.append(f"This is {name}:")
        contents.append(file_to_part(upload_file))

    # Add final instruction
    contents.append(prompt)

    # SHOW contents for debugging
    print("Contents for image generation:")
    for content in contents:
        if isinstance(content, str):
            print("Text:", content)
        elif isinstance(content, types.Part):
            print("Part with mime type:", content.inline_data.mime_type)
        else:
            print("Unknown content type")

    response = google_client.models.generate_content(
        model="gemini-2.5-flash-image-preview",
        contents=contents,
        config=types.GenerateContentConfig(
            image_config=types.ImageConfig(
                aspect_ratio="9:16",
            )
        )
    )

    print("Full response:", response)
    print("Candidates:", response.candidates)
    if response.candidates:
        print("First candidate content:", response.candidates[0].content)
        print("Parts:", response.candidates[0].content.parts)


    for part in response.candidates[0].content.parts:
        if part.text is not None:
            print(part.text)
        elif part.inline_data is not None:
            image = Image.open(BytesIO(part.inline_data.data))
            output_dir = os.path.join(directory, f"{filename}.png")  # Safer path construction
            if os.path.exists(output_dir):
                try:
                    os.remove(output_dir)
                    print(f"Removed existing file: {output_dir}")
                except OSError as e:
                    print(f"Error removing existing file {output_dir}: {e}")
                    continue  # Skip saving if removal fails (optional)
            try:
                image.save(output_dir)
                print(f"Saved image to: {output_dir}")
            except Exception as e:
                print(f"Error saving image to {output_dir}: {e}")

    return f"{directory}/{filename}.png"


def generate_video(directory="static/videos/", filename="video", prompt="Generate", negative_prompt="", image_path=None, duration: int = 3):
    os.makedirs(directory, exist_ok=True)
    output_path = os.path.join(directory, f"{filename}.mp4")

    url = "https://api.runware.ai/v1/video/generate"
    headers = {
        "Authorization": f"Bearer {RUNWARE_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "taskType": "videoInference",
        "taskUUID": str(uuid.uuid4()),
        "model": "bytedance:1@1",
        "positivePrompt": prompt,
        "duration": duration,
        "outputType": "URL",       # ✅ only URL allowed
        "outputFormat": "mp4",
        "height": height,
        "width": width,
        "deliveryMethod": "async",
    }

    image_data_uri = None
    if image_path:
        if not os.path.exists(image_path):
            raise ValueError(f"Image path not found: {image_path}")
        
        with open(image_path, "rb") as f:
            img_bytes = f.read()
        
        # Detect MIME type
        mime_type, _ = mimetypes.guess_type(image_path)
        if mime_type is None:
            # Fallback to extension
            ext = os.path.splitext(image_path)[1].lower()
            if ext == '.png':
                mime_type = 'image/png'
        
        if not mime_type.startswith('image/') or mime_type.split('/')[-1] not in ['png', 'jpeg', 'webp']:
            raise ValueError(f"Unsupported image MIME type: {mime_type}")
        
        # Construct data URI with detected MIME type
        image_data_uri = f"data:{mime_type};base64,{base64.b64encode(img_bytes).decode('utf-8')}"
        print("Including image in payload")
        payload["frameImages"] = [{"inputImage": image_data_uri}]

    # Wrap in array as required by Runware
    request_body = [payload]

    response = requests.post(url, headers=headers, json=request_body, timeout=120)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Runware API error: {response.text}")

    result = response.json()
    print("Runware API response:", json.dumps(result, indent=2))
    if "errors" in result and result["errors"]:
        raise HTTPException(status_code=500, detail=f"Runware API errors: {result['errors']}")
    if "data" not in result or not result["data"]:
        raise HTTPException(status_code=500, detail=f"Unexpected Runware response: {result}")

    print("Polling started...")

    if "url" not in result["data"][0]:
        print("Task is pending, polling for result...")
        task_uuid = result["data"][0]["taskUUID"]
        print(f"Extracted task UUID: {task_uuid}")
        poll_url = "https://api.runware.ai/v1/task"  # Use base task endpoint
        max_attempts = 15
        poll_interval = 5

        poll_headers = {
            "Authorization": f"Bearer {RUNWARE_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # JSON payload for polling
        poll_payload = [{
            "taskUUID": task_uuid,
            "taskType": "getResponse",
        }]

        for attempt in range(max_attempts):
            time.sleep(poll_interval)
            try:
                print(f"Polling attempt {attempt + 1}/{max_attempts} for task UUID: {task_uuid}")
                poll_response = requests.post(poll_url, headers=poll_headers, json=poll_payload, timeout=30)
                poll_response.raise_for_status()
                poll_result = poll_response.json()
                print(f"Polling response: {json.dumps(poll_result, indent=2)}")

                if "data" in poll_result and poll_result["data"]:
                    if poll_result["data"][0].get("status") == "success":
                        video_url = poll_result["data"][0].get("videoURL")
                        if not video_url:
                            raise ValueError("Task completed but no video URL found")
                        print(f"Video URL retrieved: {video_url}")
                        break
                    elif poll_result["data"][0].get("taskStatus") == "FAILED":
                        raise HTTPException(status_code=500, detail=f"Video generation failed: {poll_result['data'][0].get('error', 'Unknown error')}")
            except requests.exceptions.HTTPError as e:
                print(f"Polling attempt {attempt + 1} failed with HTTP error: {e}")
                print(f"Response body: {poll_response.text}")
                if attempt == max_attempts - 1:
                    raise HTTPException(status_code=500, detail=f"Polling failed after {max_attempts} attempts: {e}")
            except requests.exceptions.RequestException as e:
                print(f"Polling attempt {attempt + 1} failed: {e}")
                if attempt == max_attempts - 1:
                    raise HTTPException(status_code=500, detail=f"Polling failed after {max_attempts} attempts: {e}")
        else:
            raise HTTPException(status_code=500, detail=f"Video generation timed out after {max_attempts * poll_interval} seconds")
    else:
        video_url = result["data"][0]["videoURL"]

    # Download video from URL to local storage
    r = requests.get(video_url, stream=True, timeout=300)
    r.raise_for_status()
    with open(output_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    return output_path

def filename_from_name(name: str) -> str:
    return name.lower().replace(" ", "_")