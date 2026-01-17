from fastapi import APIRouter, Depends, Body, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from pydantic import BaseModel
from sqlalchemy.future import select

import json

from db import get_session, Voiceover
from services import generate_speech, filename_from_name

router = APIRouter(prefix="/voiceovers", tags=["voiceovers"])

class VoiceoverUpdate(BaseModel):
    start_time: float



@router.post("/{project_id}")
async def create_voiceover(project_id: str, session: AsyncSession = Depends(get_session)):   
    new_voiceover = Voiceover(project_id=project_id, duration=5.0, start_time=0.0, text="DEFAULT TEXT")
    session.add(new_voiceover)
    await session.commit()
    await session.refresh(new_voiceover)
    return new_voiceover


@router.post("/combine/{project_id}")
async def combine_voiceovers(project_id: str, session: AsyncSession = Depends(get_session)):
    """
    Combine all voiceovers for a given project into a single voiceover.
    """

    result = await session.execute(
        select(Voiceover).where(Voiceover.project_id == project_id)
    )
    voiceovers = result.scalars().all()

    combined_text = " ".join([" ".join(vo.text.split(" ")) for vo in voiceovers])
    # CREATE NEW VOICEOVER (DO NOT GENERATE THE AUDIO YET)
    new_voiceover = Voiceover(project_id=project_id, duration=0.0, start_time=0.0, text=combined_text)
    session.add(new_voiceover)
    await session.commit()
    await session.refresh(new_voiceover)
    return new_voiceover



@router.delete("/{voiceover_id}")
async def delete_voiceover(
    voiceover_id: str,
    session: AsyncSession = Depends(get_session)
):
    # Fetch the voiceover
    voiceover = await session.get(Voiceover, voiceover_id)
    
    if not voiceover:
        raise HTTPException(status_code=404, detail="Voiceover not found")

    # Optional: Add authorization check here if needed
    # e.g., check if voiceover.project.user_id == current_user.id

    # Delete the voiceover (SQLAlchemy will handle cascade if configured)
    await session.delete(voiceover)
    await session.commit()

    return {
        "success": True,
        "message": "Voiceover deleted successfully",
        "voiceover_id": voiceover_id
    }

@router.post("/{voiceover_id}")
async def update_voiceover_start_time(
    voiceover_id: str,
    payload: VoiceoverUpdate,
    session: AsyncSession = Depends(get_session)
):
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
async def generate_voiceover(voiceover_id: str, request: VoiceoverGenerateRequest, session: AsyncSession = Depends(get_session)):
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