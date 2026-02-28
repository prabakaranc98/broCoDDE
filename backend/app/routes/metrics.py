"""
BroCoDDE — Metrics and Observatory Routes
POST /tasks/{id}/metrics — log post-mortem metrics
GET  /observatory — aggregate analytics for Observatory view
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import CoddeTask, PublishedPost
from app.memory.store import compute_performance_patterns

router = APIRouter()


class MetricsInput(BaseModel):
    impressions: int = 0
    saves: int = 0
    comments: int = 0
    dms: int = 0
    reposts: int = 0
    profile_visits: int = 0
    platform: str = "linkedin"
    content: str | None = None


class ObservatoryResponse(BaseModel):
    total_posts: int
    avg_impressions: float
    avg_saves: float
    avg_save_rate: float
    avg_comments: float
    best_archetype: str | None
    posts: list[dict[str, Any]]
    patterns: dict[str, Any]


@router.post("/tasks/{task_id}/metrics", status_code=201)
async def log_metrics(
    task_id: str,
    data: MetricsInput,
    db: AsyncSession = Depends(get_db),
):
    """Log post-mortem metrics for a published task. Creates a PublishedPost record."""
    task = await db.get(CoddeTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    metrics = {
        "impressions": data.impressions,
        "saves": data.saves,
        "comments": data.comments,
        "dms": data.dms,
        "reposts": data.reposts,
        "profile_visits": data.profile_visits,
        "save_rate": round(data.saves / data.impressions, 4) if data.impressions > 0 else 0.0,
    }

    post = PublishedPost(
        task_id=task_id,
        content=data.content or task.final_content or "",
        platform=data.platform,
        metrics=metrics,
    )
    db.add(post)

    # Advance task to post-mortem stage if it was in ready
    if task.stage == "ready":
        task.stage = "post-mortem"
        task.published_at = datetime.utcnow()

    await db.flush()
    return {"task_id": task_id, "metrics": metrics, "post_id": post.id}


@router.get("/observatory", response_model=ObservatoryResponse)
async def get_observatory(db: AsyncSession = Depends(get_db)):
    """Return aggregate performance analytics for the Observatory view."""
    result = await db.execute(
        select(PublishedPost).order_by(PublishedPost.published_at.desc())
    )
    posts = list(result.scalars().all())

    if not posts:
        return ObservatoryResponse(
            total_posts=0,
            avg_impressions=0,
            avg_saves=0,
            avg_save_rate=0,
            avg_comments=0,
            best_archetype=None,
            posts=[],
            patterns={},
        )

    all_impressions = [p.metrics.get("impressions", 0) for p in posts]
    all_saves = [p.metrics.get("saves", 0) for p in posts]
    all_comments = [p.metrics.get("comments", 0) for p in posts]
    n = len(posts)

    avg_imp = sum(all_impressions) / n
    avg_sav = sum(all_saves) / n
    avg_com = sum(all_comments) / n
    avg_save_rate = avg_sav / avg_imp if avg_imp > 0 else 0.0

    patterns = await compute_performance_patterns(db)
    best_arch = patterns.archetype_performance[0].archetype if patterns.archetype_performance else None

    posts_data = []
    for p in posts:
        task = await db.get(CoddeTask, p.task_id)
        posts_data.append({
            "task_id": p.task_id,
            "title": task.title if task else "",
            "role": task.role if task else "",
            "archetype": task.archetype if task else "",
            "domain": task.domain if task else "",
            "published_at": p.published_at.isoformat() if p.published_at else None,
            **p.metrics,
        })

    return ObservatoryResponse(
        total_posts=n,
        avg_impressions=round(avg_imp, 1),
        avg_saves=round(avg_sav, 1),
        avg_save_rate=round(avg_save_rate, 4),
        avg_comments=round(avg_com, 1),
        best_archetype=best_arch,
        posts=posts_data,
        patterns=patterns.model_dump(),
    )
