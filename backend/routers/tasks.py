from huey.api import Result
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from worker import generate_scene_video_task   # ← this is key

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.get("/{task_id}")
async def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    Check status of a background task by its ID
    Returns current state + result/error if finished
    """
    huey = generate_scene_video_task.huey

    try:
        result: Result = huey.result(task_id, preserve=True)  # preserve=True keeps it even after get

        if result is None:
            # Task still running / queued
            return {
                "task_id": task_id,
                "status": "pending",           # or "queued" / "processing"
                "result": None,
                "error": None
            }

        if isinstance(result, Exception):
            return {
                "task_id": task_id,
                "status": "failed",
                "result": None,
                "error": str(result),
                "traceback": result.__traceback__  # optional
            }

        # Success!
        return {
            "task_id": task_id,
            "status": "success",
            "result": result,                  # your return value
            "error": None
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error checking task status: {str(e)}"
        )