from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.api.deps import SessionDep
from app.schemas.music import CreateMusicIn, DuplicateMusicIn, MusicOut, UpdateMusicIn, UploadMusicOut
from app.services import music_service
from app.services.errors import NotFoundError

router = APIRouter(prefix="/music", tags=["music"])


@router.post("/{project_id}", response_model=MusicOut)
async def create_music(project_id: str, body: CreateMusicIn, session: SessionDep):
    music = await music_service.create_music(session, project_id, body.start_time)
    return MusicOut.from_model(music)


@router.post("/{music_id}/duplicate", response_model=MusicOut)
async def duplicate_music(music_id: str, session: SessionDep, body: Optional[DuplicateMusicIn] = None):
    try:
        music = await music_service.duplicate_music(session, music_id, body or DuplicateMusicIn())
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return MusicOut.from_model(music)


@router.put("/upload-music/{music_id}", response_model=UploadMusicOut)
async def upload_music(music_id: str, session: SessionDep, music_file: UploadFile = File(...)):
    try:
        music = await music_service.upload_music(session, music_id, music_file)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return UploadMusicOut(message="Music uploaded successfully", music=MusicOut.from_model(music))


@router.put("/{music_id}", response_model=MusicOut)
async def update_music(music_id: str, body: UpdateMusicIn, session: SessionDep):
    try:
        music = await music_service.set_music_source(session, music_id, body.src)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return MusicOut.from_model(music)


@router.delete("/{music_id}")
async def delete_music(music_id: str, session: SessionDep):
    await music_service.delete_music(session, music_id)
    return {"message": "Music deleted successfully"}
