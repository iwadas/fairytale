from fastapi import APIRouter, HTTPException, Body, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
import uuid

import os
from db import get_session, Project, Scene
from schemas import ProjectBasicOutput, ProjectOutput
from moviepy import VideoFileClip, concatenate_videoclips, AudioFileClip, CompositeAudioClip

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("/download/{project_id}")
async def download_project(project_id: str, session: AsyncSession = Depends(get_session)):
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
    # Placeholder for actual download logic

    # Define output directory and ensure it exists
    output_dir = "videos"  # Relative path; adjust as needed
    output_filename = "combined_video.mp4"
    output_path = os.path.join(output_dir, output_filename)

    # Step 1: Load and concatenate the video clips
    video_clips = [VideoFileClip(path) for path in [scene.video_src for scene in project.scenes if scene.video_src]]
    final_video = concatenate_videoclips(video_clips)

    # Step 2: Prepare the voiceover audio clips with start times
    voiceover_clips = [AudioFileClip(path).with_start(start_time) for path, start_time in [(vo.src, vo.start_time) for vo in project.voiceovers if vo.src]]

    # Step 3: Get the original video audio (if present) and composite with voiceovers
    video_audio = final_video.audio if final_video.audio else None
    all_audios = [video_audio] + voiceover_clips if video_audio else voiceover_clips
    composite_audio = CompositeAudioClip(all_audios)

    # Step 4: Combine video with the composite audio
    final_clip = final_video.with_audio(composite_audio)

    # Step 5: Write the final video to file
    final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")

    # Clean up clips to free memory
    final_clip.close()
    for clip in video_clips + voiceover_clips + ([video_audio] if video_audio else []):
        clip.close()

    return {"message": f"Download for project {project_id} initiated"}

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