import os

from fastapi import APIRouter, Body, UploadFile, File, HTTPException

from services import save_file
from database.crud import create_music_db, get_music_db, update_music_db, delete_music_db

from typing import Optional

from pydub import AudioSegment

router = APIRouter(prefix="/music", tags=["music"])

@router.post("/{project_id}")
async def create_music(
    project_id: str,
    start_time: float = Body(..., embed=True),    
):   
    return await create_music_db(project_id=project_id, start_time=start_time)


@router.post("/{music_id}/duplicate")
async def duplicate_music(
    music_id: str,
    
    start_time: Optional[float] = Body(0.0, embed=True),
    cut_start: Optional[float] = Body(0.0, embed=True),
    cut_end: Optional[float] = Body(0.0, embed=True),
    duration: Optional[float] = Body(0.0, embed=True),
    layer: Optional[int] = Body(2, embed=True),
    
):
    music = await get_music_db(music_id)
    if not music:
        raise HTTPException(status_code=404, detail="Music not found")

    new_music = await create_music_db(
        project_id=music["project_id"],
        src=music["src"],
        name=music["name"],

        duration=duration or music["duration"],
        start_time=start_time or music["start_time"] + music["duration"],
        cut_start=cut_start or music["cut_start"],
        cut_end=cut_end or music["cut_end"],
        layer=layer or music["layer"],
    )
    return new_music

# HELPER FUNCTION TO GET DURATION
def get_audio_duration(audio_file_path: str) -> float:
    if not os.path.exists(audio_file_path):
        return 0.0
    try:
        audio = AudioSegment.from_file(audio_file_path)
        return len(audio) / 1000.0
    except Exception as e:
        print(f"Error calculating duration: {e}")
        return 0.0

@router.put("/upload-music/{music_id}")
async def upload_music(
    music_id: str,
    music_file: UploadFile = File(...),
):
    music = await get_music_db(music_id)
    if not music:
        raise HTTPException(status_code=404, detail="Music not found")
    
    src = await save_file(music_file, type="music")

    duration = get_audio_duration(src)

    updated_music = await update_music_db(
        id=music_id,
        src=src,
        name=music_file.filename.replace(" ", "_"),
        duration=duration
    )
    return {"message": "Music uploaded successfully", "music": updated_music}

@router.put("/{music_id}")
async def update_music(
    music_id: str,
    src: str = Body(..., embed=True),
):
    music = await get_music_db(music_id)
    if not music:
        raise HTTPException(status_code=404, detail="Music not found")
    

    duration = get_audio_duration(src)

    updated_music = await update_music_db(
        id=music_id,
        name=src.split("/")[-1].replace(" ", "_"),
        src=src,
        duration=duration
    )

    return updated_music




@router.delete("/{music_id}")
async def delete_music(
    music_id: str,
):
    await delete_music_db(id=music_id)
    return {"message": "Music deleted successfully"}
   