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

from google import genai  
from google.genai import types
from elevenlabs import ElevenLabs, save
from dotenv import load_dotenv

load_dotenv()
GENAI_API_KEY = os.getenv("GENAI_API_KEY")
RUNWARE_API_KEY = os.getenv("RUNWARE_API_KEY")
ELEVEN_LABS_API_KEY = os.getenv("ELEVEN_LABS_API_KEY")

google_client = genai.Client(api_key=GENAI_API_KEY)
eleven_labs_client = ElevenLabs(api_key=ELEVEN_LABS_API_KEY)

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

def generate_speech(text: str, filename="voiceover", directory="static/voiceovers/"):
    audio = eleven_labs_client.text_to_speech.convert(
        text=text,
        voice_id="21m00Tcm4TlvDq8ikWAM",  # example voice (Rachel)
        model_id="eleven_multilingual_v2"
    )

    # Make sure the directory exists
    os.makedirs(directory, exist_ok=True)

    # Build full file path
    output_path = os.path.join(directory, f"{filename}.mp3")

    # Write audio chunks to file
    with open(output_path, "wb") as f:
        for chunk in audio:
            f.write(chunk)

    return output_path

def generate_image(directory="static/images/default/", filename="image", prompt="Generate", content_images: dict = {}):
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
    )

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
        "height": 480,
        "width": 864,
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