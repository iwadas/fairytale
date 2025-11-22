import asyncio
from fastapi import APIRouter, HTTPException, Body, UploadFile, File, Depends, Form, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict
from pathlib import Path
import os
import re

# MoviePy imports
from moviepy import ImageClip, VideoClip, vfx, ColorClip, CompositeVideoClip
import numpy as np

from pydantic import BaseModel

from db import get_session, Scene, Character
from services import generate_image, generate_image_banana, generate_video, filename_from_name, create_typing_video, height, width

router = APIRouter(prefix="/scenes", tags=["scenes"])


class TypingSceneRequest(BaseModel):
    text: str

@router.post("/generate-typing-scene/{scene_id}")
async def generate_typing_scene(
    scene_id: str,
    payload: TypingSceneRequest,
    session: AsyncSession = Depends(get_session),
):

    scene = await session.get(Scene, scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    
    my_text = payload.text if payload.text else "This is a typing effect demo."
    output_filename = create_typing_video(my_text, duration=scene.duration, output_filename=f'static/videos/scenes/{scene_id}_typing.mp4')

    scene.video_src = output_filename
    scene.video_prompt = f"Typing effect: {my_text}"
    scene.image_prompt = f"Typing effect: {my_text}"
    session.add(scene)
    await session.commit()
    await session.refresh(scene)
    return {"message": "Typing effect video generated successfully", "scene_id": scene_id, "video_url": output_filename}


@router.delete("/{scene_id}")
async def delete_scene(scene_id: str, session: AsyncSession = Depends(get_session)):
    # 1. Get scene from DB using ORM
    scene = await session.get(Scene, scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    # 2. Delete scene from DB
    await session.delete(scene)
    await session.commit()
    return {"message": "Scene deleted successfully"}


def _parse_ref_images(request_form: Dict[str, UploadFile]) -> Dict[str, UploadFile]:
    ref: Dict[str, UploadFile] = {}
    for key, file in request_form.items():
        if key.startswith("reference_images[") and key.endswith("]"):
            name = key[len("reference_images[") : -1]   # strip brackets
            ref[name] = file
    return ref

@router.post("/generate-image/{scene_id}")
async def generate_scene_image(
    scene_id: str,
    files: Optional[List[UploadFile]] = File(None),  # Catch ALL files
    lowkey: bool = Form(False),
    image_prompt: str = Form(...),
    session: AsyncSession = Depends(get_session),
):
    # Now, files[] contains ALL uploaded files
    # But we need to know which file belongs to which scene_id
    # → We use the **original filename** or **custom header** to map

    ref_images_dict = {}

    if files and len(files):
        for file in files:
            # Option 1: Use filename to extract scene_id
            # Assume filename is: scene_<uuid>.png
            match = re.search(r"scene_([a-f0-9-]+)", file.filename or "")
            if match:
                name = match.group(1)
                content = await file.read()
                print(f"  → {name}: {file.filename} ({len(content)} bytes)")
                ref_images_dict[name] = file
                await file.seek(0)  # Reset for later

    print(f"Got {len(ref_images_dict)} reference images")

    filename = filename_from_name(f"scene_{scene_id}")

    # 3. Call your image generator
    print("Generating image with prompt:", image_prompt)

    # if content_image are empty, we use generate_image, if not we use generate_image_banana
    image_path = generate_image_banana(
        directory="static/images/scenes",
        filename=filename,
        prompt=image_prompt,
        content_images={},
    )

    scene = await session.get(Scene, scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    scene.image_src = image_path
    scene.image_prompt = image_prompt
    session.add(scene)

    await session.commit()
    # optionally refresh scene/image
    await session.refresh(scene)

    return {"message": "Scene image generated successfully", "scene_id": scene_id, "image_url": image_path}

    # ------------------------------------------------------------------
    # 2. Extract lowkey
    # ------------------------------------------------------------------
    print(f"\nlowkey = {lowkey!r}")

    # ------------------------------------------------------------------
    # 3. Build a clean dict of reference images
    # ------------------------------------------------------------------
    ref_images = _parse_ref_images(request.form)

    print("\n=== REFERENCE IMAGES ===")
    if not ref_images:
        print("  (none)")
    else:
        for name, upload in ref_images.items():
            # read a tiny chunk just to prove we can access the file
            first_kb = await upload.read(1024)
            await upload.seek(0)          # reset for later use
            print(
                f"  [{name}]  size={upload.size or 'unknown'}  "
                f"type={upload.content_type}  first_kb={len(first_kb)} bytes"
            )

    # ------------------------------------------------------------------
    # 4. (Optional) Return a JSON summary – super handy in Postman/Insomnia
    # ------------------------------------------------------------------


    # 4. Store or update scene image in DB (attach to scene)
    scene = await session.get(Scene, scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    scene.image_src = image_path
    scene.image_prompt = prompt
    session.add(scene)

    await session.commit()
    # optionally refresh scene/image
    await session.refresh(scene)
    return {"message": "Scene image generated successfully", "scene_id": scene_id, "image_url": image_path}

@router.put("/upload-image/{scene_id}")
async def upload_scene_image(
    scene_id: str,
    image: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
):
    # 1. Get scene from DB using ORM
    scene = await session.get(Scene, scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    # 2. Generate filename for scene
    filename = filename_from_name(f"scene_{scene_id}")

    # 3. Save uploaded image to disk
    output_dir = "static/images/scenes"
    os.makedirs(output_dir, exist_ok=True)
    image_path = os.path.join(output_dir, f"{filename}.png")  # Safer path construction
    try:
        with open(image_path, "wb") as f:
            f.write(image.file.read())
        print(f"Saved uploaded image to: {image_path}")
    except Exception as e:
        print(f"Error saving uploaded image to {image_path}: {e}")
        raise HTTPException(status_code=500, detail="Failed to save uploaded image")

    # 4. Store or update scene image in DB (attach to scene)
    scene.image_src = image_path
    session.add(scene)

    await session.commit()
    await session.refresh(scene)  # Refresh to confirm the update

    return {"message": "Scene image uploaded successfully", "scene_id": scene_id, "image_url": image_path}

@router.post("/generate-scene-video/{scene_id}")
async def generate_scene_video(
    scene_id: str,
    prompt: str = Body(..., embed=True),
    session: AsyncSession = Depends(get_session),
):
    # 1. Get scene image path from DB using ORM
    scene = await session.get(Scene, scene_id)
    print("Scene ID for video generation:", scene_id)
    if not scene:
        print("Scene not found")
        raise HTTPException(status_code=404, detail="Scene not found")
    if not scene.image_src or not Path(scene.image_src).exists():
        print("Scene image not found")
        raise HTTPException(status_code=400, detail="Scene image not found. Generate scene image first.")
    
    # 2. Generate filename for scene video
    filename = filename_from_name(f"scene_{scene_id}")

    # 3. Call the video generator
    print("Scene ID:", scene_id)
    print("Generating video with prompt:", prompt)
    print("Using scene image:", scene.image_src)
    print("Scene duration:", scene.duration)
    print("Generating video...")

    video_path = generate_video(
        directory="static/videos/scenes",
        filename=filename,
        prompt=prompt,
        negative_prompt="",  # Default to empty string, adjust if needed
        image_path=scene.image_src,
        duration=scene.duration  # Default duration, adjust as needed
    )

    # 4. Store or update scene video in DB (attach to scene)
    scene.video_src = video_path
    scene.video_prompt = prompt
    session.add(scene)

    await session.commit()

    # Optionally refresh scene/video
    await session.refresh(scene)

    return {"message": "Scene video generated successfully", "scene_id": scene_id, "video_url": video_path}


@router.post("/add-character-to-scene")
async def add_character_to_scene(
    scene_id: str = Body(..., embed=True),
    character_id: str = Body(..., embed=True),
    session: AsyncSession = Depends(get_session),
):
    # Fetch the scene with its characters relationship pre-loaded
    result = await session.execute(
        select(Scene).options(selectinload(Scene.characters)).filter_by(id=scene_id)
    )
    scene = result.scalars().first()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    # Fetch the character
    character = await session.get(Character, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    # Check if the character is already associated with the scene
    if character in scene.characters:
        raise HTTPException(status_code=400, detail="Character is already in the scene")

    # Add the character to the scene's characters relationship
    scene.characters.append(character)

    # Commit the transaction
    session.add(scene)
    await session.commit()
    await session.refresh(scene)

    return {"message": f"Character {character_id} added to scene {scene_id}"}


@router.post("/add-effect-to-image/{scene_id}")
async def add_effect_to_image(
    scene_id: str,
    effect: str = Body(..., embed=True),
    session: AsyncSession = Depends(get_session),
):
    # 1. Get scene from DB using ORM
    scene = await session.get(Scene, scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    if not scene.image_src or not Path(scene.image_src).exists():
        raise HTTPException(status_code=400, detail="Scene image not found. Generate scene image first.")

    # Ensure output directory exists
    output_dir = Path("static/videos/scenes")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = str(output_dir / f"output_{scene_id}_{effect}.mp4")

    duration = scene.duration if scene.duration else 5.0  # Default to 5 seconds if not set

    print(f"Applying effect '{effect}' to image '{scene.image_src}' for duration {duration}s, saving to '{output_path}'")

    loop = asyncio.get_running_loop()

    def _process_sync(image_path: str, effect_name: str, out_path: str, duration_s: float) -> str:
        """Synchronous worker to run MoviePy (runs in threadpool). Returns output path."""

        image_clip: Optional[ImageClip] = None
        result_clip: Optional[VideoClip] = None

        video_size = (width, height)

        try:
            # Create ImageClip with duration
            image_clip = ImageClip(image_path).with_duration(duration_s)

            if effect_name == "zoom_in":
                # Zoom-in: scale from 1.0 -> 2.0 linearly, with center crop/pad to fixed size
                print("Applying zoom_in effect")

                def make_frame(t):
                    scale = 1.0 + 0.2 * (t / duration_s)  # 1.0 -> 1.2
                    temp = image_clip.resized(scale)
                    temp_fixed = CompositeVideoClip([ColorClip(video_size, color=(0, 0, 0)), temp.with_position('center')])
                    return temp_fixed.get_frame(t)

                result_clip = VideoClip(make_frame).with_duration(duration_s).with_fps(24)
                print("Zoom_in effect applied")

            elif effect_name == "pan":
                # Pan left->right across the image at output crop size
                img_w, img_h = image_clip.size
                crop_w, crop_h = video_size

                # Ensure image width is at least 1.1x output width for smooth panning
                min_width = int(crop_w * 1.1)
                if img_w < min_width or img_h < crop_h:
                    # Calculate scale to ensure width is at least min_width and height is at least crop_h
                    scale_w = min_width / img_w
                    scale_h = crop_h / img_h
                    scale = max(scale_w, scale_h)  # Preserve aspect ratio
                    image_resized = image_clip.resized(scale)
                    img_w, img_h = image_resized.size
                    print(f"Resized image from ({image_clip.size[0]}, {image_clip.size[1]}) to ({img_w}, {img_h}) for pan effect")
                else:
                    image_resized = image_clip

                def make_frame(t):
                    x = (img_w - crop_w) * (t / duration_s)  # Pan from left to right
                    # Center vertically if taller
                    y1 = (img_h - crop_h) / 2 if img_h > crop_h else 0
                    temp = image_resized.cropped(x1=x, y1=y1, x2=x + crop_w, y2=y1 + crop_h)
                    return temp.get_frame(t)

                result_clip = VideoClip(make_frame).with_duration(duration_s).with_fps(24)

            elif effect_name == "rotate":
                # Rotate from 0 -> 90 degrees, without expanding canvas (keeps fixed size)
                result_clip = image_clip.rotated(lambda t: 90 * (t / duration_s), expand=False).with_fps(24)

            elif effect_name == "fade":
                # Fade in/out
                fade_duration = min(duration_s / 5.0, 0.5)
                result_clip = (
                    image_clip
                    .with_effects([vfx.FadeIn(duration=fade_duration), vfx.FadeOut(duration=fade_duration)])
                    .with_fps(24)
                )

            elif effect_name == "color_adjust":
                # Per-frame brightness increase from factor 1.0 -> 1.5
                def make_frame(t):
                    frame = image_clip.get_frame(t).astype("float32")
                    factor = 1.0 + 0.5 * (t / duration_s)
                    frame *= factor
                    np.clip(frame, 0, 255, out=frame)
                    return frame.astype("uint8")

                result_clip = VideoClip(make_frame, duration=duration_s).with_fps(24)

            else:
                raise ValueError(f"Unsupported effect: {effect_name}")

            # Pad with black or center-crop to exact video size without stretching
            result_clip = CompositeVideoClip([ColorClip(video_size, color=(0, 0, 0)), result_clip.with_position('center')]).with_duration(duration_s).with_fps(24)

            # Write the file
            result_clip.write_videofile(
                out_path,
                codec="libx264",
                fps=24,
                audio=False,
                ffmpeg_params=["-vf", "format=yuv420p"],
                logger=None,
            )

            return out_path

        finally:
            # Close clips to free memory
            if result_clip:
                try:
                    result_clip.close()
                except Exception:
                    pass
            if image_clip:
                try:
                    image_clip.close()
                except Exception:
                    pass

    # Run the synchronous MoviePy work in a thread
    try:
        output_file = await loop.run_in_executor(None, _process_sync, scene.image_src, effect, output_path, duration)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to process video: {exc}")
    

    # 4. Store or update scene video in DB (attach to scene)
    scene.video_src = output_file
    session.add(scene)
    await session.commit()
    await session.refresh(scene)  # Refresh to confirm the update

    return {"message": "Video generated successfully", "video_path": output_file}