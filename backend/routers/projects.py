from fastapi import APIRouter, HTTPException, Body, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from sqlalchemy.orm import selectinload
import uuid

import os
from typing import List, Dict, Tuple, Set
from db import get_session, Project, Scene, Voiceover
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
    return
    
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
    return
    
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
    return
    new_project = Project(id=str(uuid.uuid4()), name=name)
    session.add(new_project)
    await session.commit()
    await session.refresh(new_project)
    return {"project_id": new_project.id}

@router.delete("/{project_id}")
async def delete_project(project_id: str, session: AsyncSession = Depends(get_session)):
    return
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
    return project


def diff_by_id(
    old: List[Dict],
    new: List[Dict],
) -> Tuple[Set[str], List[Dict], List[Dict]]:
    """
    Returns:
        deleted_ids: set of ids that exist in old but not in new
        to_insert:   rows that are in new but not in old (no id match)
        to_update:   rows that exist in both but have different values
    """
    old_map = {item["id"]: item for item in old}
    new_map = {item["id"]: item for item in new}

    deleted = old_map.keys() - new_map.keys()

    to_insert = []
    to_update = []

    for nid, nitem in new_map.items():
        if nid not in old_map:
            to_insert.append(nitem)
        else:
            oitem = old_map[nid]
            # deep comparison – ignore keys that are always generated (e.g. src after generation)
            if oitem != nitem:
                to_update.append(nitem)

    return deleted, to_insert, to_update

@router.put("/{project_id}")
async def update_project(
    project_id: str,
    scenes: list = Body(...),
    voiceovers: list = Body(...),
    session: AsyncSession = Depends(get_session)
):
    # === Load current scenes (only scalar fields for diff) ===
    result = await session.execute(
        select(Scene).where(Scene.project_id == project_id)
    )
    cur_scenes = result.scalars().all()

    cur_scenes_dict = [
        {
            "id": s.id,
            "project_id": s.project_id,
            "image_prompt": s.image_prompt,
            "image_src": s.image_src,
            "start_time": s.start_time,
            "duration": s.duration,
            "video_prompt": s.video_prompt,
            "video_src": s.video_src,
        }
        for s in cur_scenes
    ]

    # === Load voiceovers ===
    result = await session.execute(
        select(Voiceover).where(Voiceover.project_id == project_id)
    )
    cur_voiceovers = result.scalars().all()
    cur_voiceovers_dict = [v.__dict__ for v in cur_voiceovers]

    # === Diff ===
    del_sc_ids, ins_sc, upd_sc = diff_by_id(cur_scenes_dict, scenes)
    del_vo_ids, ins_vo, upd_vo = diff_by_id(cur_voiceovers_dict, voiceovers)

    # === DELETE ===
    if del_sc_ids:
        await session.execute(
            delete(Scene).where(Scene.id.in_(del_sc_ids))
        )

    if del_vo_ids:
        await session.execute(
            delete(Voiceover).where(Voiceover.id.in_(del_vo_ids))
        )

    # === INSERT SCENES (only scalar fields) ===
    if ins_sc:
        new_scenes = []
        for row in ins_sc:
            # Remove relationship fields
            row.pop("characters", None)
            row.pop("places", None)
            new_scenes.append(Scene(**row, project_id=project_id))
        session.add_all(new_scenes)

    # === UPDATE SCENES (only scalar fields) ===
    if upd_sc:
        for row in upd_sc:
            # Remove relationship fields
            row.pop("characters", None)
            row.pop("places", None)
            # Create minimal Scene instance with only scalar fields
            scene = Scene(**row)
            await session.merge(scene)  # Safe: no relationships touched

    # === VOICEOVERS (no relationships) ===
    if ins_vo:
        session.add_all([Voiceover(**row, project_id=project_id) for row in ins_vo])

    if upd_vo:
        for row in upd_vo:
            await session.merge(Voiceover(**row))

    await session.commit()

    return {
        "updated": len(upd_sc) + len(upd_vo),
        "inserted": len(ins_sc) + len(ins_vo),
        "deleted": len(del_sc_ids) + len(del_vo_ids),
    }