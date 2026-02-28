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
        select(CoddeTask).where(CoddeTask.series_id == series_id)
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
        "tasks": [{"id": t.id, "title": t.title, "stage": t.stage} for t in tasks],
    }
