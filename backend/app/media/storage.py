# save_file.py
import uuid
import os
import aiofiles
from dotenv import load_dotenv
from fastapi import UploadFile, HTTPException
import cv2
import numpy as np


def remove_gemini_watermark_if_present(image_bytes: bytes) -> bytes | None:
    """
    Attempts to detect and remove a Gemini-style bottom-right watermark from an image.
    Returns cleaned image bytes (PNG) if watermark was likely present and removed,
    or None if no watermark was detected or removal was not applied.
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    print("1-------")
    if img is None:
        return None

    h, w = img.shape[:2]

    # Define watermark region (Gemini 2048×2048 case or fallback)
    if w == 2048 and h == 2048:
        crop_start = (1888, 1888)
        crop_end   = (1983, 1983)
    else:
        crop_start = (w - 96, h - 96)
        crop_end   = (w - 1, h - 1)

    print(f"Image size: {w}x{h}, cropping region: {crop_start} to {crop_end}")

    # Safety bounds check
    print("2-------")

    if (crop_start[0] < 0 or crop_start[1] < 0 or
        crop_end[0] >= w or crop_end[1] >= h or
        crop_start[0] >= crop_end[0] or crop_start[1] >= crop_end[1]):
        return None

    crop = img[crop_start[1]:crop_end[1]+1, crop_start[0]:crop_end[0]+1]

    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)

    # Threshold tuned for semi-transparent white-ish watermark
    thresh_value = 120
    _, thresh = cv2.threshold(gray, thresh_value, 255, cv2.THRESH_BINARY)

    # Light morphology to reduce noise
    bright_ratio = (np.sum(thresh == 255) / thresh.size) * 100

    # Typical detection window: ~20–55% bright pixels in that small region
    if not (18 < bright_ratio < 55):
        print(f"No strong watermark detected (bright pixels: {bright_ratio:.1f}%) – skipping removal.")
        return None
    
    print(f"Watermark detected (bright pixels: {bright_ratio:.1f}%) – removing...")

    # Crop from bottom — most conservative approach
    keep_h = crop_start[1]

    # Optional: prefer even height
    if keep_h % 2 == 1:
        keep_h -= 1

    # Optional symmetric side crop (many prefer to skip this)
    side_crop = (w - keep_h) // 2
    if side_crop > 0:
        cleaned = img[:keep_h, side_crop : w - side_crop]
    else:
        cleaned = img[:keep_h, :]

    # Encode back to PNG bytes
    success, buffer = cv2.imencode(".png", cleaned)
    if not success:
        return None

    return buffer.tobytes()


async def save_file(
    file: UploadFile,
    type: str = "scene",
    remove_watermark_if_present: bool = False
) -> str:
    """
    Saves uploaded file.
    For scene images: optionally removes Gemini-style watermark if requested and detected.
    """
    load_dotenv()

    # Determine output directory and default extension
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

    os.makedirs(output_dir, exist_ok=True)

    filename = f"scene_{uuid.uuid4()}"
    src = os.path.join(output_dir, f"{filename}.{ext}")

    try:
        content = await file.read()

        # Watermark removal — only for images + flag enabled
        if type == "scene_image" and remove_watermark_if_present:
            cleaned_bytes = remove_gemini_watermark_if_present(content)
            if cleaned_bytes is not None:
                content = cleaned_bytes
                # Ensure we save as .png after processing
                src = os.path.join(output_dir, f"{filename}.png")

        # Save final content
        async with aiofiles.open(src, "wb") as f:
            await f.write(content)

        print(f"Saved file to: {src}")
        return src

    except Exception as e:
        print(f"Error processing/saving file {src}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save uploaded file")