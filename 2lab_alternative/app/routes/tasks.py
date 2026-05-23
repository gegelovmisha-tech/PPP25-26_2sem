from fastapi import APIRouter, HTTPException
from celery.result import AsyncResult
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.tasks import celery_app, rebuild_stats, reimport_source

router = APIRouter(prefix="/tasks", tags=["tasks"])

class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str

class TaskStatus(BaseModel):
    task_id: str
    status: str
    progress: Optional[int] = None
    message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@router.post("/rebuild_stats", response_model=TaskResponse)
async def start_rebuild_stats(source_id: int = None):
    task = rebuild_stats.delay(source_id)
    return TaskResponse(
        task_id=task.id,
        status="pending",
        message=f"Task started. Check /tasks/{task.id} for status"
    )

@router.post("/reimport_source/{source_id}", response_model=TaskResponse)
async def start_reimport_source(source_id: int):
    task = reimport_source.delay(source_id)
    return TaskResponse(
        task_id=task.id,
        status="pending",
        message=f"Reimport task started for source {source_id}"
    )

@router.get("/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    task_result = AsyncResult(task_id, app=celery_app)
    
    status = task_result.state
    result = task_result.result if task_result.successful() else None
    error = str(task_result.info) if task_result.failed() else None
    
    meta = {}
    if task_result.info and isinstance(task_result.info, dict):
        meta = task_result.info
    
    return TaskStatus(
        task_id=task_id,
        status=status.lower(),
        progress=meta.get("progress"),
        message=meta.get("message") or meta.get("error"),
        result=result if task_result.successful() else None,
        error=error
    )

@router.get("/")
async def list_tasks():
    return {"message": "Use GET /tasks/{task_id} to check specific task"}
