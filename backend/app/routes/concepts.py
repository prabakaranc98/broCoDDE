"""
BroCoDDE — Concept Nodes API Routes
CRUD for the personal knowledge graph built via Spark/Feynman sessions.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import ConceptNode

router = APIRouter()


class ConceptCreate(BaseModel):
    title: str
    core_insight: str
    source_url: str | None = None
    source_title: str | None = None
    domain: str | None = None
    tags: list[str] = []
    task_id: str | None = None


class ConceptUpdate(BaseModel):
    title: str | None = None
    core_insight: str | None = None
    source_url: str | None = None
    source_title: str | None = None
    domain: str | None = None
    tags: list[str] | None = None
    connections: list[str] | None = None


class ConceptResponse(BaseModel):
    id: str
    title: str
    core_insight: str
    source_url: str | None
    source_title: str | None
    domain: str | None
    tags: list[str]
    connections: list[str]
    task_id: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


@router.get("", response_model=list[ConceptResponse])
async def list_concepts(
    domain: str | None = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    query = select(ConceptNode).order_by(ConceptNode.created_at.desc()).limit(limit)
    if domain:
        query = query.where(ConceptNode.domain == domain)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("", response_model=ConceptResponse, status_code=201)
async def create_concept(data: ConceptCreate, db: AsyncSession = Depends(get_db)):
    concept = ConceptNode(**data.model_dump())
    db.add(concept)
    await db.flush()
    await db.refresh(concept)
    return concept


@router.get("/{concept_id}", response_model=ConceptResponse)
async def get_concept(concept_id: str, db: AsyncSession = Depends(get_db)):
    concept = await db.get(ConceptNode, concept_id)
    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")
    return concept


@router.patch("/{concept_id}", response_model=ConceptResponse)
async def update_concept(
    concept_id: str,
    data: ConceptUpdate,
    db: AsyncSession = Depends(get_db),
):
    concept = await db.get(ConceptNode, concept_id)
    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(concept, field, value)
    concept.updated_at = datetime.utcnow()
    await db.flush()
    return concept


@router.delete("/{concept_id}")
async def delete_concept(concept_id: str, db: AsyncSession = Depends(get_db)):
    concept = await db.get(ConceptNode, concept_id)
    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")
    await db.delete(concept)
    await db.commit()
    return {"ok": True}


@router.get("/search/query", response_model=list[ConceptResponse])
async def search_concepts(q: str, db: AsyncSession = Depends(get_db)):
    """Keyword search across title, core_insight, and domain."""
    from sqlalchemy import or_
    result = await db.execute(
        select(ConceptNode)
        .where(or_(
            ConceptNode.title.ilike(f"%{q}%"),
            ConceptNode.core_insight.ilike(f"%{q}%"),
            ConceptNode.domain.ilike(f"%{q}%"),
        ))
        .order_by(ConceptNode.created_at.desc())
        .limit(5)
    )
    return list(result.scalars().all())
