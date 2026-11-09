from typing import Optional

from fastapi import APIRouter, HTTPException

from app.api.deps import SessionDep
from app.schemas.project import (
    CopyProjectOut,
    CreateProjectOut,
    ProjectIn,
    ProjectListItem,
    ProjectRecord,
    ScriptIn,
    ScriptsOut,
    TimelineUpdateIn,
)
from app.services import project_service

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectListItem])
async def get_projects(session: SessionDep):
    projects = await project_service.list_projects(session)
    return [ProjectListItem.from_model(project, thumbnail) for project, thumbnail in projects]


@router.get("/{project_id}", response_model=Optional[ProjectRecord])
async def get_project(project_id: str, session: SessionDep):
    project = await project_service.get_project(session, project_id)
    return ProjectRecord.model_validate(project) if project else None


@router.post("/generate-script", response_model=ScriptsOut)
async def script_generation(request: ScriptIn):
    try:
        scripts = await project_service.generate_scripts(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return ScriptsOut(scripts=scripts)


@router.post("/create-project", response_model=CreateProjectOut)
async def create_project(project_in: ProjectIn, session: SessionDep):
    project_id = await project_service.create_project(session, topic=project_in.topic, script=project_in.script)
    return CreateProjectOut(message="Project created successfully", project_id=project_id)


@router.delete("/{project_id}")
async def delete_project(project_id: str, session: SessionDep):
    await project_service.delete_project(session, project_id)
    return {"message": "Project deleted successfully"}


@router.put("/{project_id}")
async def update_project(body: TimelineUpdateIn, session: SessionDep):
    await project_service.update_timeline(session, body.timeline_elements)
    return {"message": "Update successful"}


@router.post("/download/{project_id}")
async def download_project(project_id: str, session: SessionDep):
    await project_service.render_project(session, project_id)
    return {"message": "success"}


# TODO: translations are not implemented (see app/api/routers/translations.py, unmounted).
@router.post("/add-translations/{project_id}")
async def add_translations(project_id: str):
    return None


@router.post("/copy/{project_id}", response_model=CopyProjectOut)
async def copy_project(project_id: str, session: SessionDep):
    new_project = await project_service.copy_project(session, project_id)
    return CopyProjectOut(success=True, new_project_id=new_project.id, message="Project copied successfully")
