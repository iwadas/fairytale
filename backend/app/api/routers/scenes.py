from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Body, File, Form, HTTPException, UploadFile

from app.api.deps import SessionDep
from app.schemas.scene import (
    AddCharacterToSceneIn,
    CreateSceneIn,
    DuplicateSceneIn,
    FixImagePromptIn,
    FixVideoPromptIn,
    GenerateImagePromptsIn,
    GenerateSceneVideoIn,
    SceneImageOut,
    SceneOut,
)
from app.services import scene_service
from app.services.errors import NotFoundError

router = APIRouter(prefix="/scenes", tags=["scenes"])


@router.post("/generate-image-prompts")
async def generate_scene_image_prompt(body: GenerateImagePromptsIn, session: SessionDep):
    descriptions = await scene_service.generate_image_prompts(
        session, body.project_id, body.selected_voiceover_text_part, body.additional_info
    )
    return {"new_scene_descriptions": descriptions}


@router.post("/fix-image-prompt")
async def fix_image_prompt(body: FixImagePromptIn):
    fixed_prompt = await scene_service.fix_image_prompt(body.scene_prompt, body.style, body.style_power)
    return {"fixed_prompt": fixed_prompt}


@router.post("/{scene_id}/duplicate", response_model=SceneOut)
async def duplicate_scene(scene_id: str, session: SessionDep, body: Optional[DuplicateSceneIn] = None):
    try:
        scene = await scene_service.duplicate_scene(session, scene_id, body or DuplicateSceneIn())
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return SceneOut.from_model(scene)


# NOTE (audit B6): registered before /add-character-to-scene, so it also matches that path.
@router.post("/{project_id}", response_model=SceneOut)
async def create_scene(project_id: str, session: SessionDep, body: Optional[CreateSceneIn] = None):
    body = body or CreateSceneIn()
    scene = await scene_service.create_scene(session, project_id, body.start_time)
    return SceneOut.from_model(scene)


@router.delete("/{scene_id}")
async def delete_scene(scene_id: str, session: SessionDep):
    await scene_service.delete_scene(session, scene_id)
    return {"message": "Scene deleted successfully"}


# TODO: image generation is not implemented.
@router.post("/generate-image/{scene_id}")
async def generate_scene_image(
    scene_id: str,
    files: Optional[List[UploadFile]] = File(None),  # Catch ALL files
    lowkey: bool = Form(False),
    prompt: str = Form(...),
    scene_image_id: Optional[str] = Form(None),
    time: Optional[str] = Form(None),
):
    return None


@router.put("/upload-video/{scene_id}")
async def upload_scene_video(scene_id: str, session: SessionDep, video: UploadFile = File(...)):
    try:
        video_src, duration = await scene_service.upload_scene_video(session, scene_id, video)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"message": "Scene video uploaded successfully", "video_src": video_src, "duration": duration}


@router.delete("/remove-image/{scene_image_id}")
async def remove_scene_image(scene_image_id: str, session: SessionDep):
    await scene_service.remove_scene_image(session, scene_image_id)
    return {"message": "Scene image removed successfully", "scene_image_id": scene_image_id}


# Multipart form: the Body() fields below are read from the form data.
@router.put("/upload-image/{scene_id}")
async def upload_scene_image(
    scene_id: str,
    session: SessionDep,
    time: str = Body(..., embed=True),
    scene_image_id: Optional[str] = Body(None, embed=True),
    scene_image_prompt: Optional[str] = Body(None, embed=True),
    image: UploadFile = File(...),
):
    try:
        scene_image = await scene_service.upload_scene_image(
            session, scene_id, image, time=time, scene_image_id=scene_image_id, scene_image_prompt=scene_image_prompt
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"message": "Scene image uploaded successfully", "scene_image": SceneImageOut.from_model(scene_image)}


@router.post("/generate-video/{scene_id}")
async def generate_scene_video(
    background_tasks: BackgroundTasks,
    scene_id: str,
    body: GenerateSceneVideoIn,
    session: SessionDep,
):
    try:
        frames = await scene_service.prepare_video_generation(session, scene_id)
    except NotFoundError as e:
        raise HTTPException(404, str(e))

    background_tasks.add_task(scene_service.process_video_task, scene_id, body.prompt, body.duration, frames)
    return {"message": "Video generation started in background"}


@router.post("/fix-video-prompt/{scene_id}", response_model=SceneOut)
async def fix_video_prompt(scene_id: str, body: FixVideoPromptIn, session: SessionDep):
    try:
        scene = await scene_service.fix_video_prompt(session, scene_id, body.new_camera_movement, body.additional_info)
    except NotFoundError as e:
        raise HTTPException(404, str(e))
    # Wire compatibility: this response has always been sent without the images.
    return SceneOut.from_model(scene, with_images=False)


# TODO: not implemented, and unreachable anyway (shadowed by POST /{project_id}, audit B6).
@router.post("/add-character-to-scene")
async def add_character_to_scene(body: AddCharacterToSceneIn):
    return None
