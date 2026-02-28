"""
BroCoDDE — CoDDE-Task API Routes
POST /tasks — create a new CoDDE-task
GET  /tasks — list tasks (with optional filters)
GET  /tasks/{id} — get a single task
PATCH /tasks/{id}/stage — advance lifecycle stage
PATCH /tasks/{id} — update task fields
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import CoddeTask

router = APIRouter()

VALID_STAGES = [
    "discovery", "extraction", "structuring",
    "drafting", "vetting", "ready", "post-mortem",
]


# ── Pydantic Schemas ──────────────────────────────────────────────────────────

class TaskCreate(BaseModel):
    role: str
    intent: str
    domain: str | None = None
    series_id: str | None = None
    title: str | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    archetype: str | None = None
    domain: str | None = None
    series_id: str | None = None
    skeleton: dict | None = None
    final_content: str | None = None


class StageUpdate(BaseModel):
    stage: str


class TaskResponse(BaseModel):
    id: str
    title: str | None
    role: str | None
    intent: str | None
    archetype: str | None
    domain: str | None
    series_id: str | None
    stage: str
    lint_results: dict | None
    skeleton: dict | None
    chat_history: list[dict] | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _generate_task_id() -> str:
    now = datetime.utcnow()
    import random
    return f"codde-{now.strftime('%Y%m%d')}-{random.randint(100, 999)}"


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("", response_model=TaskResponse, status_code=201)
async def create_task(data: TaskCreate, db: AsyncSession = Depends(get_db)):
    task = CoddeTask(
        id=_generate_task_id(),
        role=data.role,
        intent=data.intent,
        domain=data.domain,
        series_id=data.series_id,
        title=data.title,
        stage="discovery",
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)
    return task


@router.get("", response_model=list[TaskResponse])
async def list_tasks(
    stage: str | None = None,
    series_id: str | None = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    query = select(CoddeTask).order_by(CoddeTask.created_at.desc()).limit(limit)
    if stage:
        query = query.where(CoddeTask.stage == stage)
    if series_id:
        query = query.where(CoddeTask.series_id == series_id)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, db: AsyncSession = Depends(get_db)):
    task = await db.get(CoddeTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task


@router.patch("/{task_id}/stage", response_model=TaskResponse)
async def advance_stage(
    task_id: str,
    data: StageUpdate,
    db: AsyncSession = Depends(get_db),
):
    task = await db.get(CoddeTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    if data.stage not in VALID_STAGES:
        raise HTTPException(status_code=400, detail=f"Invalid stage: {data.stage}")
    task.stage = data.stage
    task.updated_at = datetime.utcnow()
    await db.flush()
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    data: TaskUpdate,
    db: AsyncSession = Depends(get_db),
):
    task = await db.get(CoddeTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(task, field, value)
    task.updated_at = datetime.utcnow()
    await db.flush()
    return task


@router.post("/{task_id}/drafts")
async def save_draft(
    task_id: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
):
    """Append a draft version to the task's drafts list."""
    task = await db.get(CoddeTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    drafts = list(task.drafts or [])
    drafts.append({
        "version": len(drafts) + 1,
        "content": body.get("content", ""),
        "created_at": datetime.utcnow().isoformat(),
    })
    task.drafts = drafts
    task.updated_at = datetime.utcnow()
    await db.flush()
    return {"version": len(drafts), "saved": True}
