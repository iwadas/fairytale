from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_session, Voiceover
from services import generate_speech, filename_from_name

router = APIRouter(prefix="/voiceovers", tags=["voiceovers"])

@router.post("/generate-voiceover/{voiceover_id}")
async def generate_voiceover(voiceover_id: str, session: AsyncSession = Depends(get_session)):
    voiceover = await session.get(Voiceover, voiceover_id)

    if not voiceover:
        raise ValueError("Voiceover not found")
    if not voiceover.text:
        raise ValueError("Voiceover text is empty")

    filename = filename_from_name(f"voiceover_{voiceover_id}")
    audio_path = generate_speech(
        text=voiceover.text,
        filename=filename,
        directory="static/voiceovers"
    )

    voiceover.src = audio_path
    session.add(voiceover)
    await session.commit()
    await session.refresh(voiceover)
    return {"message": "Voiceover generated successfully", "voiceover_id": voiceover_id, "voiceover_src": audio_path}