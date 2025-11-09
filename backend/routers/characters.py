from fastapi import APIRouter, HTTPException, Body, UploadFile, File, Form, Depends
from fastapi.responses import FileResponse
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pathlib import Path
import uuid

from db import get_session, Character
from schemas import CharacterOutput
from services import generate_image, filename_from_name

router = APIRouter(prefix="/characters", tags=["characters"])

@router.get("/images/{character_id}")
async def get_character_image(character_id: str, session: AsyncSession = Depends(get_session)):
    character = await session.get(Character, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    if not character.src or not Path(character.src).exists():
        raise HTTPException(status_code=404, detail="Image file not found")
    return FileResponse(character.src, media_type="image/png")

@router.post("")
async def create_character(
    name: str = Form(...),
    prompt: str = Form(...),
    image1: UploadFile = File(...),
    image2: Optional[UploadFile] = File(None),
    session: AsyncSession = Depends(get_session),
):
    # build content_images
    content_images = {"image1": image1}
    if image2:
        content_images["image2"] = image2

    image_path = await generate_image(
        directory=f"static/images/characters",
        filename=filename_from_name(name),
        prompt=prompt,
        content_images=content_images,
        lowkey=False
    )

    new_char = Character(id=str(uuid.uuid4()), name=name, prompt=prompt, src=image_path)
    session.add(new_char)
    await session.commit()
    await session.refresh(new_char)
    return {"message": "Character created successfully", "character_id": new_char.id, "image_path": image_path}

@router.put("/{character_id}")
async def update_character(
    character_id: str,
    name: Optional[str] = Body(None),
    prompt: Optional[str] = Body(None),
    image1: Optional[UploadFile] = File(None),
    image2: Optional[UploadFile] = File(None),
    session: AsyncSession = Depends(get_session),
):
    character = await session.get(Character, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    if name is not None:
        character.name = name
    if prompt is not None:
        character.prompt = prompt

    if image1:
        content_images = {"image1": image1}
        if image2:
            content_images["image2"] = image2
        image_path = await generate_image(
            directory=f"static/images/characters",
            filename=filename_from_name(name or character.name),
            prompt=prompt or character.prompt or "update",
            content_images=content_images,
            lowkey=False
        )
        character.src = image_path

    session.add(character)
    await session.commit()
    await session.refresh(character)
    return {"message": f"Character {character_id} updated successfully", "new_src": image_path}

@router.get("")
async def list_characters(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Character))
    characters = result.scalars().all()
    # Return list of Pydantic objects or raw dicts
    return [CharacterOutput.model_validate(c).model_dump() for c in characters]

@router.delete("/{character_id}")
async def delete_character(character_id: str, session: AsyncSession = Depends(get_session)):
    character = await session.get(Character, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    await session.delete(character)
    await session.commit()
    return {"message": f"Character {character_id} deleted"}