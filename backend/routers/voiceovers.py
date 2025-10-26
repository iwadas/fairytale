from fastapi import APIRouter, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession

from pydantic import BaseModel

from db import get_session, Voiceover
from services import generate_speech, filename_from_name

router = APIRouter(prefix="/voiceovers", tags=["voiceovers"])

class VoiceoverUpdate(BaseModel):
    start_time: float

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



@router.post("/generate-voiceover/{voiceover_id}")
async def generate_voiceover(voiceover_id: str, session: AsyncSession = Depends(get_session)):
    voiceover = await session.get(Voiceover, voiceover_id)

    if not voiceover:
        raise ValueError("Voiceover not found")
    if not voiceover.text:
        raise ValueError("Voiceover text is empty")

    filename = filename_from_name(f"voiceover_{voiceover_id}")
    print("Generating voiceover for text:")
    audio_path, duration = generate_speech(
        text=voiceover.text,
        filename=filename,
        directory="static/voiceovers"
    )
    print("Generating stopped voiceover for text:")

    voiceover.src = audio_path
    voiceover.duration = duration
    session.add(voiceover)
    await session.commit()
    await session.refresh(voiceover)
    return {"message": "Voiceover generated successfully", "voiceover_id": voiceover_id, "voiceover_src": audio_path, "duration": duration}