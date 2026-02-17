from fastapi import APIRouter, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession

from pydantic import BaseModel
from database.crud import create_voiceover_db, get_project_voiceovers_db, remove_voiceover_db, get_voiceover_db, update_voiceover_db

from db import get_session, Voiceover
from AI.tts import TTS

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


# NOT USED (maybe used in future for auto-updating project)
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


@router.post("/generate/{voiceover_id}")
async def generate_voiceover(
    voiceover_id: str, 
    text: str = Body(..., embed=True),
):
    voiceover = get_voiceover_db(id=voiceover_id)
    if not voiceover:
        raise ValueError("Voiceover not found")
    if not voiceover["text"]:
        raise ValueError("Voiceover text is empty")
    
    tts_client = TTS(
        text=text, 
        voiceover_id=voiceover_id,
        project_id=voiceover["project_id"],
        # TODO pass voice settings here
    )

    tts_result = await tts_client.generate(
        text=text,
        language="english",
        gender="female",
        voice_model_id="158880",
        age=35
    )

    await update_voiceover_db(
        **tts_result,
    )

    return {
        "message": "voiceover generated successfully",
        "voiceover_id": voiceover_id,
        "src": tts_result["src"],
    }
   