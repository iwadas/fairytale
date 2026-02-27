from fastapi import APIRouter, Body, UploadFile, File, HTTPException

from services import save_file
from database.crud import create_music_db, get_music_db, update_music_db, delete_music_db


router = APIRouter(prefix="/music", tags=["music"])

@router.post("/{project_id}")
async def create_music(project_id: str):   
    return await create_music_db(project_id=project_id)


@router.put("/upload-music/{music_id}")
async def upload_music(
    music_id: str,
    music_file: UploadFile = File(...),
):
    music = await get_music_db(music_id)
    if not music:
        raise HTTPException(status_code=404, detail="Music not found")
    
    src = await save_file(music_file, type="music")

    updated_music = await update_music_db(
        id=music_id,
        src=src,
        name=music_file.filename.replace(" ", "_")

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
    
    updated_music = await update_music_db(
        id=music_id,
        name=src.split("/")[-1].replace(" ", "_"),
        src=src
    )

    return {"message": "Music updated successfully", "music": updated_music}




@router.delete("/{music_id}")
async def delete_music(
    music_id: str,
):
    await delete_music_db(id=music_id)
    return {"message": "Music deleted successfully"}
   