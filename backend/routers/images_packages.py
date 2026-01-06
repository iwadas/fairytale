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
from worker import generate_scene_video_task


# MoviePy imports
from moviepy import ImageClip, VideoClip, vfx, ColorClip, CompositeVideoClip
import numpy as np

from pydantic import BaseModel

from db import get_session, ImagesPackage, PhotoDumpImage
from services import generate_image, generate_image_banana, generate_video, filename_from_name, create_typing_video, height, width

router = APIRouter(prefix="/images-packages", tags=["images-packages"])



@router.get("")
async def get_packages(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(ImagesPackage).options(selectinload(ImagesPackage.images)))
    packages = result.scalars().all()
    return packages

@router.get("/{package_id}")
async def get_package(package_id: str, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(ImagesPackage).where(ImagesPackage.id == package_id).options(selectinload(ImagesPackage.images)))
    package = result.scalars().first()
    if not package:
        raise HTTPException(status_code=404, detail="Images package not found")
    return package

# CREATE IMAGES PACKAGE
@router.post("")
async def create_package(session: AsyncSession = Depends(get_session)):
    # create images package
    # new name = "New Images Package" + Current Datetime
    new_name = f"New Images Package {asyncio.get_event_loop().time()}"
    new_package = ImagesPackage(name=new_name)
    session.add(new_package)

    await session.commit()
    await session.refresh(new_package)
    return new_package.id

# UPDATE IMAGES PACKAGE
@router.put("/{package_id}")
async def update_package(   
    package_id: str,
    data: Dict = Body(...),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(ImagesPackage).where(ImagesPackage.id == package_id)
    )
    images_package = result.scalars().first()
    if not images_package:
        raise HTTPException(status_code=404, detail="Images package not found")
    images_package.name = data.get("name", images_package.name)
    session.add(images_package)
    await session.commit()
    await session.refresh(images_package)
    return images_package

# DELETE IMAGES PACKAGE
@router.delete("/{package_id}")
async def delete_package(
    package_id: str,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(ImagesPackage).where(ImagesPackage.id == package_id)
    )
    images_package = result.scalars().first()
    if not images_package:
        raise HTTPException(status_code=404, detail="Images package not found")

    # Delete associated images
    for image in images_package.images:
        await session.delete(image)

    await session.delete(images_package)
    await session.commit()
    return {"detail": "Images package deleted"}

# ADD IMAGE
@router.post("/{package_id}/images")
async def add_image(
    package_id: str,
    prompt: str = Body(..., embed=True),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(ImagesPackage).where(ImagesPackage.id == package_id)
    )
    images_package = result.scalars().first()
    if not images_package:
        raise HTTPException(status_code=404, detail="Images package not found")

    # Save uploaded file to disk (you might want to change this to your desired storage)
    new_image = PhotoDumpImage(
        package_id=package_id,
        prompt=prompt,
    )
    session.add(new_image)
    await session.commit()
    await session.refresh(new_image)
    return new_image

# UPLOAD IMAGE FILE
@router.put("/upload-image/{photo_dump_image_id}")
async def upload_image_file(
    photo_dump_image_id: str,
    file: UploadFile = File(...),
    prompt: Optional[str] = Body(None, embed=True),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(PhotoDumpImage).where(PhotoDumpImage.id == photo_dump_image_id)
    )
    photo_dump_image = result.scalars().first()
    if not photo_dump_image:
        raise HTTPException(status_code=404, detail="Photo dump image not found")

    # Save uploaded file to disk (you might want to change this to your desired storage)
    filename = filename_from_name(f"{photo_dump_image.id}")
    output_dir = Path("static/images/photo_dump")
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = os.path.join(output_dir, f"{filename}.png")  # Safer path construction

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Update the PhotoDumpImage record with the file path
    photo_dump_image.src = str(file_path)
    if prompt:
        photo_dump_image.prompt = prompt
    session.add(photo_dump_image)
    await session.commit()
    await session.refresh(photo_dump_image)
    return photo_dump_image

# DELETE IMAGE
@router.delete("/images/{image_id}")
async def delete_image(
    image_id: str,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(PhotoDumpImage).where(PhotoDumpImage.id == image_id)
    )
    image = result.scalars().first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    # Optionally delete the file from disk
    if image.src and os.path.exists(image.src):
        os.remove(image.src)

    await session.delete(image)
    await session.commit()
    return {"detail": "Image deleted"}