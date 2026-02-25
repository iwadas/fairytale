from fastapi import APIRouter, Body, UploadFile, File, HTTPException

from backend.services import save_file
from database.crud import create_music_db, get_music_db, update_music_db, delete_music_db


router = APIRouter(prefix="/music", tags=["music"])

@router.post("/{project_id}")
async def create_music(project_id: str):   
    return await create_music_db(project_id=project_id)


@router.put("/upload-music/{music_id}")
async def upload_music(
    music_id: str,
    image: UploadFile = File(...),
):
    music = await get_music_db(music_id)
    if not music:
        raise HTTPException(status_code=404, detail="Music not found")
    
    src = await save_file(image, type="music")

    updated_music = await update_music_db(
        id=music_id,
        src=src,
    )

    return {"message": "Music uploaded successfully", "music": updated_music}


@router.delete("/{music_id}")
async def delete_music(
    music_id: str,
):
    await delete_music_db(id=music_id)
    return {"message": "Music deleted successfully"}
   