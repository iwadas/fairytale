from fastapi import APIRouter, Depends, Body, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from pydantic import BaseModel
from sqlalchemy.future import select
from database.crud import create_voiceover_db, get_project_voiceovers_db, remove_voiceover_db

import json

from db import get_session, Voiceover
from services import generate_speech, filename_from_name

router = APIRouter(prefix="/voiceovers", tags=["voiceovers"])

class VoiceoverUpdate(BaseModel):
    start_time: float



@router.post("/{project_id}")
async def create_voiceover(project_id: str):   
    return await create_voiceover_db(project_id=project_id)

@router.post("/combine/{project_id}")
async def combine_voiceovers(project_id: str):
    """
    Combine all voiceovers for a given project into a single voiceover.
    """
    voiceovers = await get_project_voiceovers_db(project_id=project_id)
    combined_text = " ".join([" ".join(vo.text.split(" ")) for vo in voiceovers])

    # delete old voiceovers
    for vo in voiceovers:
        await remove_voiceover_db(id=vo["id"])

    return await create_voiceover_db(project_id=project_id, text=combined_text)


@router.delete("/{voiceover_id}")
async def delete_voiceover(
    voiceover_id: str,
):
    await remove_voiceover_db(id=voiceover_id)
    return {"message": "Voiceover deleted successfully"}


# NOT USED
@router.post("/{voiceover_id}")
async def update_voiceover_start_time(
    voiceover_id: str,
    payload: VoiceoverUpdate,
    session: AsyncSession = Depends(get_session)
):
    return
    voiceover = await session.get(Voiceover, voiceover_id)
    if not voiceover:
        return {"error": "Voiceover not found"}
    voiceover.start_time = payload.start_time
    session.add(voiceover)
    await session.commit()
    await session.refresh(voiceover)
    return {"message": "Voiceover start time updated", "voiceover_id": voiceover_id, "new_start_time": payload.start_time}

class VoiceoverGenerateRequest(BaseModel):
    text: str

@router.post("/generate-voiceover/{voiceover_id}")
async def generate_voiceover(
    voiceover_id: str, 
    request: VoiceoverGenerateRequest, 
    session: AsyncSession = Depends(get_session)
):

    voiceover = await session.get(Voiceover, voiceover_id)

    if not voiceover:
        raise ValueError("Voiceover not found")
    if not voiceover.text:
        raise ValueError("Voiceover text is empty")

    filename = filename_from_name(f"voiceover_{voiceover_id}")
    print("Generating voiceover for text:")
    audio_path, duration, timestamps = generate_speech(
        text=request.text,
        filename=filename,
        directory="static/voiceovers",
    )
    print("Generating stopped voiceover for text:")

    voiceover.src = audio_path
    voiceover.duration = duration
    voiceover.text = request.text
    voiceover.timestamps = json.dumps(timestamps)
    print(timestamps)
    print(json.dumps(timestamps))
    print("Before commit - timestamps:", voiceover.timestamps)

    session.add(voiceover)
    await session.commit()
    await session.refresh(voiceover)
    return {"message": "Voiceover generated successfully", "voiceover_id": voiceover_id, "voiceover_src": audio_path, "duration": duration, "timestamps": voiceover.timestamps}