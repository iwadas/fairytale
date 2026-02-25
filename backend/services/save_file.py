import uuid

from dotenv import load_dotenv
from fastapi import UploadFile
import os
import aiofiles
from fastapi import HTTPException

async def save_file(file: UploadFile, type: str = "scene"):
    filename = f"scene_{uuid.uuid4()}"
    load_dotenv()

    if type == "scene_video":
        output_dir = os.getenv("SCENE_VIDEO_DIR", "static/videos/scenes")
        ext = "mp4"
    elif type == "scene_image":
        output_dir = os.getenv("SCENE_IMAGE_DIR", "static/images/scenes")
        ext = "png"
    elif type == "music":
        output_dir = os.getenv("MUSIC_DIR", "static/music")
        ext = "mp3"
    else:
        raise ValueError(f"Invalid file type: {type}")
    
    # if type includes image -> ext = png, else ext = mp4
    
    video_src = os.path.join(output_dir, f"{filename}.{ext}")

    try:
        async with aiofiles.open(video_src, "wb") as f:
            await f.write(file.file.read())
        print(f"Saved uploaded file to: {video_src}")
        return video_src
    except Exception as e:
        print(f"Error saving uploaded file to {video_src}: {e}")
        raise HTTPException(status_code=500, detail="Failed to save uploaded file")