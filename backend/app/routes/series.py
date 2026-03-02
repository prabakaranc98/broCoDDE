"""
BroCoDDE — Series API Routes
CRUD for content series.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import CoddeTask, Series

router = APIRouter()


class SeriesCreate(BaseModel):
    name: str
    description: str | None = None
    archetype: str | None = None
    icon: str | None = None
    target_post_count: int = 5


class SeriesResponse(BaseModel):
    id: str
    name: str
    description: str | None
    archetype: str | None
    icon: str | None
    target_post_count: int
    post_count: int = 0
    progress_pct: float = 0.0

    model_config = {"from_attributes": True}


@router.get("", response_model=list[SeriesResponse])
async def list_series(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Series).order_by(Series.created_at.desc()))
    series_list = result.scalars().all()

    out = []
    for s in series_list:
        tasks_result = await db.execute(
            select(CoddeTask).where(CoddeTask.series_id == s.id)
        )
        task_count = len(tasks_result.scalars().all())
        progress = round(task_count / s.target_post_count * 100, 1) if s.target_post_count else 0
        out.append(SeriesResponse(
            id=s.id,
            name=s.name,
            description=s.description,
            archetype=s.archetype,
            icon=s.icon,
            target_post_count=s.target_post_count,
            post_count=task_count,
            progress_pct=min(progress, 100.0),
        ))
    return out


@router.post("", response_model=SeriesResponse, status_code=201)
async def create_series(data: SeriesCreate, db: AsyncSession = Depends(get_db)):
    series = Series(**data.model_dump())
    db.add(series)
    await db.flush()
    await db.refresh(series)
    return SeriesResponse(**series.__dict__, post_count=0, progress_pct=0.0)


@router.get("/{series_id}")
async def get_series(series_id: str, db: AsyncSession = Depends(get_db)):
    series = await db.get(Series, series_id)
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    tasks_result = await db.execute(
        select(CoddeTask).where(CoddeTask.series_id == series_id).order_by(CoddeTask.created_at.desc())
    )
    tasks = tasks_result.scalars().all()
    return {
        "id": series.id,
        "name": series.name,
        "description": series.description,
        "archetype": series.archetype,
        "icon": series.icon,
        "target_post_count": series.target_post_count,
        "post_count": len(tasks),
        "progress_pct": round(min(len(tasks) / series.target_post_count * 100, 100), 1) if series.target_post_count else 0,
        "tasks": [{"id": t.id, "title": t.title or "Untitled", "stage": t.stage} for t in tasks],
    }


class SeriesUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    archetype: str | None = None
    icon: str | None = None
    target_post_count: int | None = None


@router.patch("/{series_id}", response_model=SeriesResponse)
async def update_series(series_id: str, data: SeriesUpdate, db: AsyncSession = Depends(get_db)):
    series = await db.get(Series, series_id)
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(series, field, value)
    await db.commit()
    tasks_result = await db.execute(select(CoddeTask).where(CoddeTask.series_id == series_id))
    count = len(tasks_result.scalars().all())
    progress = round(min(count / series.target_post_count * 100, 100), 1) if series.target_post_count else 0
    return SeriesResponse(**series.__dict__, post_count=count, progress_pct=progress)


@router.delete("/{series_id}")
async def delete_series(series_id: str, db: AsyncSession = Depends(get_db)):
    series = await db.get(Series, series_id)
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    # Unlink tasks (set series_id=None) rather than cascade-delete tasks
    tasks_result = await db.execute(select(CoddeTask).where(CoddeTask.series_id == series_id))
    for task in tasks_result.scalars().all():
        task.series_id = None
    await db.delete(series)
    await db.commit()
    return {"ok": True}


@router.patch("/{series_id}/tasks/{task_id}")
async def assign_task_to_series(series_id: str, task_id: str, db: AsyncSession = Depends(get_db)):
    """Assign an existing task to this series (or move it from another series)."""
    series = await db.get(Series, series_id)
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    task = await db.get(CoddeTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.series_id = series_id
    await db.commit()
    return {"ok": True, "task_id": task_id, "series_id": series_id}


@router.delete("/{series_id}/tasks/{task_id}")
async def remove_task_from_series(series_id: str, task_id: str, db: AsyncSession = Depends(get_db)):
    """Remove a task from this series (unlink, don't delete)."""
    task = await db.get(CoddeTask, task_id)
    if not task or task.series_id != series_id:
        raise HTTPException(status_code=404, detail="Task not in this series")
    task.series_id = None
    await db.commit()
    return {"ok": True}
