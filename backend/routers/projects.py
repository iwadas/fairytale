from fastapi import APIRouter, HTTPException, Body, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from sqlalchemy.orm import selectinload
import uuid

import os
from db import get_session, Project, Scene
from schemas import ProjectBasicOutput, ProjectOutput
from moviepy import VideoFileClip, concatenate_videoclips, AudioFileClip, CompositeAudioClip

router = APIRouter(prefix="/projects", tags=["projects"])

@router.post("/add-scene/{project_id}")
async def add_scene_to_project(
    project_id: str,
    scene_number: int = Body(...),
    image_prompt: str = Body(...),
    video_prompt: str = Body(...),
    duration: int = Body(...),
    session: AsyncSession = Depends(get_session)
):
    # ADD + 1 TO ALL SCENES >= scene_number
    project = await session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await session.execute(
            update(Scene)
            .where(Scene.project_id == project_id)
            .where(Scene.scene_number >= scene_number)
            .values(scene_number=Scene.scene_number + 1)
        )

    new_scene = Scene(
        id=str(uuid.uuid4()),
        scene_number=scene_number,
        image_prompt=image_prompt if image_prompt else "None",
        video_prompt=video_prompt if video_prompt else "None",
        duration=duration if duration else 5,
        project_id=project_id
    )
    session.add(new_scene)
    await session.commit()
    await session.refresh(new_scene)
    return {
        "message": f"New scene: {new_scene.id} added to project {project_id}",
        "scene": new_scene
    }

@router.post("/download/{project_id}")
async def download_project(project_id: str, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Project)
        .where(Project.id == project_id)
        .options(
            selectinload(Project.scenes).selectinload(Scene.characters),
            selectinload(Project.scenes).selectinload(Scene.places),
            selectinload(Project.places),
            selectinload(Project.characters),
            selectinload(Project.voiceovers),
        )
    )
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Define output directory and ensure it exists
    output_dir = "videos"
    os.makedirs(output_dir, exist_ok=True)
    output_filename = "combined_video.mp4"
    output_path = os.path.join(output_dir, output_filename)

    # ✅ Step 1: Sort scenes by scene_number and concatenate videos
    ordered_scenes = sorted(
        [scene for scene in project.scenes if scene.video_src],
        key=lambda s: s.scene_number
    )
    video_clips = [VideoFileClip(scene.video_src) for scene in ordered_scenes]
    final_video = concatenate_videoclips(video_clips)

    # ✅ Calculate total project duration
    total_duration = sum(scene.duration for scene in project.scenes if scene.duration)

    # ✅ Step 2: Add background music (clipped to match project duration)
    music_path = "./static/default/sounds/13_angels.mp3"
    if os.path.exists(music_path):
        print("Adding background music")
        background_music = AudioFileClip(music_path).subclipped(0, total_duration)
    else:
        print("Background music file not found, skipping")
        background_music = None

    # Step 3: Prepare voiceover audio clips with start times
    voiceover_clips = []
    for vo in project.voiceovers:
        if vo.src:
            clip = AudioFileClip(vo.src).with_start(vo.start_time)
            voiceover_clips.append(clip)

    # Step 4: Combine all audio sources
    video_audio = final_video.audio if final_video.audio else None
    all_audios = [a for a in [video_audio, background_music] if a] + voiceover_clips
    composite_audio = CompositeAudioClip(all_audios)

    # Step 5: Combine video with composite audio
    final_clip = final_video.with_audio(composite_audio)

    # Step 6: Write the final video to file
    final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")

    # Clean up to free memory
    final_clip.close()
    for clip in video_clips + voiceover_clips + [c for c in [video_audio, background_music] if c]:
        clip.close()

    return {"message": f"Download for project {project_id} completed"}

@router.post("")
async def create_project(name: str = Body(...), session: AsyncSession = Depends(get_session)):
    new_project = Project(id=str(uuid.uuid4()), name=name)
    session.add(new_project)
    await session.commit()
    await session.refresh(new_project)
    return {"project_id": new_project.id}

@router.delete("/{project_id}")
async def delete_project(project_id: str, session: AsyncSession = Depends(get_session)):
    project = await session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await session.delete(project)
    await session.commit()
    return {"message": f"Project {project_id} deleted"}

@router.get("")
async def list_projects(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Project))
    projects = result.scalars().all()
    return [ProjectBasicOutput.model_validate(p).model_dump() for p in projects]

@router.get("/{project_id}")
async def get_project(project_id: str, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Project)
        .where(Project.id == project_id)
        .options(
            selectinload(Project.scenes)
                .selectinload(Scene.characters),
            selectinload(Project.scenes)
                .selectinload(Scene.places),
            selectinload(Project.places),
            selectinload(Project.characters),
            selectinload(Project.voiceovers),
        )
    )
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    # serialize with Pydantic
    return ProjectOutput.model_validate(project).model_dump()