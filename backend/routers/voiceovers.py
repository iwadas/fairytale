from fastapi import APIRouter, Body

from database.crud import create_voiceover_db, get_project_voiceovers_db, remove_voiceover_db, get_voiceover_db, update_voiceover_db

from AI.tts import TTS

from websocket import WebSocketTaskManager 

import uuid

router = APIRouter(prefix="/voiceovers", tags=["voiceovers"])

@router.post("/{project_id}")
async def create_voiceover(
    project_id: str,
    start_time: float = Body(0.0, embed=True),    
):   
    return await create_voiceover_db(project_id=project_id, text="", start_time=start_time)

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


@router.post("/generate/{voiceover_id}")
async def generate_voiceover(
    voiceover_id: str, 
    text: str = Body(..., embed=True),
):
    voiceover = await get_voiceover_db(id=voiceover_id)
    if not voiceover:
        raise ValueError("Voiceover not found")
    if not voiceover["text"]:
        raise ValueError("Voiceover text is empty")
    
    tts_client = await TTS.create()

    task = WebSocketTaskManager(connection_type="global", message_type="voiceover_generation")

    await task.send_json(
        message=f"🎙️ Initializing voiceover generation...",
        status="init"
    )

    print("Generating voiceover with text:", text)

    tts_result = await tts_client.generate(
        progress_callback=task.send_json,
        text=text,
    )

    print("TTS result:", tts_result)

    await task.send_json(
        message=f"📁 Saving generated voiceover...",
        status="in_progress"
    )

    await update_voiceover_db(
        id=voiceover_id,
        **tts_result
    )

    await task.send_json(
        message=f"✅ Voiceover generation and saving completed.",
        status="finished"
    )

    return {
        "message": "voiceover generated successfully",
        "voiceover_id": voiceover_id,
        "src": tts_result["src"],
        "duration": tts_result["duration"],
        "timestamps": tts_result["timestamps"]
    }
   