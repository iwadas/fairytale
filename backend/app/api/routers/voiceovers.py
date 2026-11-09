from typing import Optional

from fastapi import APIRouter, HTTPException

from app.api.deps import SessionDep
from app.schemas.voiceover import (
    CreateVoiceoverIn,
    DuplicateVoiceoverIn,
    GenerateVoiceoverIn,
    GenerateVoiceoverOut,
    VoiceoverOut,
)
from app.services import voiceover_service
from app.services.errors import NotFoundError

router = APIRouter(prefix="/voiceovers", tags=["voiceovers"])


@router.post("/{project_id}", response_model=VoiceoverOut)
async def create_voiceover(project_id: str, session: SessionDep, body: Optional[CreateVoiceoverIn] = None):
    body = body or CreateVoiceoverIn()
    voiceover = await voiceover_service.create_voiceover(session, project_id, body.start_time)
    return VoiceoverOut.from_model(voiceover)


@router.post("/{voiceover_id}/duplicate", response_model=VoiceoverOut)
async def duplicate_voiceover(voiceover_id: str, session: SessionDep, body: Optional[DuplicateVoiceoverIn] = None):
    try:
        voiceover = await voiceover_service.duplicate_voiceover(session, voiceover_id, body or DuplicateVoiceoverIn())
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return VoiceoverOut.from_model(voiceover)


@router.post("/combine/{project_id}", response_model=VoiceoverOut)
async def combine_voiceovers(project_id: str, session: SessionDep):
    """Combine all voiceovers for a given project into a single voiceover."""
    voiceover = await voiceover_service.combine_voiceovers(session, project_id)
    return VoiceoverOut.from_model(voiceover)


@router.delete("/{voiceover_id}")
async def delete_voiceover(voiceover_id: str, session: SessionDep):
    await voiceover_service.delete_voiceover(session, voiceover_id)
    return {"message": "Voiceover deleted successfully"}


@router.post("/generate/{voiceover_id}", response_model=GenerateVoiceoverOut)
async def generate_voiceover(voiceover_id: str, body: GenerateVoiceoverIn, session: SessionDep):
    tts_result = await voiceover_service.generate_voiceover(session, voiceover_id, body.text)
    return GenerateVoiceoverOut(
        message="voiceover generated successfully",
        voiceover_id=voiceover_id,
        src=tts_result["src"],
        duration=tts_result["duration"],
        timestamps=tts_result["timestamps"],
    )
