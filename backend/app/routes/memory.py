"""
BroCoDDE — Memory API Routes
CRUD for identity memory entries and knowledge domains.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.memory.models import (
    KnowledgeDomainCreate,
    KnowledgeDomainResponse,
    MemoryEntryCreate,
    MemoryEntryResponse,
)
from app.memory.store import (
    create_domain,
    create_memory_entry,
    delete_memory_entry,
    get_domains,
    get_identity_memory,
    update_memory_entry,
)

router = APIRouter()


# ── Identity Memory (Layer 1) ─────────────────────────────────────────────────

@router.get("", response_model=list[MemoryEntryResponse])
async def list_memory(db: AsyncSession = Depends(get_db)):
    entries = await get_identity_memory(db)
    return entries


@router.post("", response_model=MemoryEntryResponse, status_code=201)
async def add_memory(data: MemoryEntryCreate, db: AsyncSession = Depends(get_db)):
    return await create_memory_entry(db, data)


@router.patch("/{entry_id}", response_model=MemoryEntryResponse)
async def edit_memory(
    entry_id: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
):
    entry = await update_memory_entry(db, entry_id, body.get("text", ""))
    if not entry:
        raise HTTPException(status_code=404, detail="Memory entry not found")
    return entry


@router.delete("/{entry_id}", status_code=204)
async def remove_memory(entry_id: str, db: AsyncSession = Depends(get_db)):
    deleted = await delete_memory_entry(db, entry_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory entry not found")


# ── Knowledge Domains (Layer 2) ───────────────────────────────────────────────

@router.get("/domains", response_model=list[KnowledgeDomainResponse])
async def list_domains(db: AsyncSession = Depends(get_db)):
    return await get_domains(db)


@router.post("/domains", response_model=KnowledgeDomainResponse, status_code=201)
async def add_domain(data: KnowledgeDomainCreate, db: AsyncSession = Depends(get_db)):
    return await create_domain(db, data)
