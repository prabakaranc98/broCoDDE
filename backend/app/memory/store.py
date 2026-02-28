"""
BroCoDDE — Memory Store (CRUD for all 6 memory layers)
"""

from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CoddeTask, KnowledgeDomain, MemoryEntry, PublishedPost
from app.memory.models import (
    ArchetypePerformance,
    ComposedContext,
    DomainResonance,
    KnowledgeDomainCreate,
    MemoryEntryCreate,
    PerformancePatterns,
)


# ── Layer 1: Identity Memory ──────────────────────────────────────────────────

async def get_identity_memory(db: AsyncSession) -> list[MemoryEntry]:
    result = await db.execute(select(MemoryEntry).order_by(MemoryEntry.created_at.desc()))
    return list(result.scalars().all())


async def create_memory_entry(db: AsyncSession, data: MemoryEntryCreate) -> MemoryEntry:
    entry = MemoryEntry(**data.model_dump())
    db.add(entry)
    await db.flush()
    await db.refresh(entry)
    return entry


async def update_memory_entry(db: AsyncSession, entry_id: str, text: str) -> MemoryEntry | None:
    entry = await db.get(MemoryEntry, entry_id)
    if not entry:
        return None
    entry.text = text
    entry.updated_at = datetime.utcnow()
    await db.flush()
    return entry


async def delete_memory_entry(db: AsyncSession, entry_id: str) -> bool:
    entry = await db.get(MemoryEntry, entry_id)
    if not entry:
        return False
    await db.delete(entry)
    return True


# ── Layer 2: Knowledge Graph ──────────────────────────────────────────────────

async def get_domains(db: AsyncSession) -> list[KnowledgeDomain]:
    result = await db.execute(select(KnowledgeDomain).order_by(KnowledgeDomain.post_count.desc()))
    return list(result.scalars().all())


async def create_domain(db: AsyncSession, data: KnowledgeDomainCreate) -> KnowledgeDomain:
    domain = KnowledgeDomain(**data.model_dump())
    db.add(domain)
    await db.flush()
    await db.refresh(domain)
    return domain


async def increment_domain_post_count(db: AsyncSession, domain_name: str):
    await db.execute(
        update(KnowledgeDomain)
        .where(KnowledgeDomain.name == domain_name)
        .values(post_count=KnowledgeDomain.post_count + 1)
    )


# ── Layer 3: Content History ──────────────────────────────────────────────────

async def get_recent_tasks(db: AsyncSession, limit: int = 10) -> list[CoddeTask]:
    result = await db.execute(
        select(CoddeTask).order_by(CoddeTask.created_at.desc()).limit(limit)
    )
    return list(result.scalars().all())


async def get_tasks_for_domain(db: AsyncSession, domain: str, limit: int = 5) -> list[CoddeTask]:
    result = await db.execute(
        select(CoddeTask)
        .where(CoddeTask.domain == domain)
        .order_by(CoddeTask.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


# ── Layer 4: Performance Patterns ─────────────────────────────────────────────

async def compute_performance_patterns(db: AsyncSession) -> PerformancePatterns:
    result = await db.execute(
        select(PublishedPost).where(PublishedPost.metrics != {})
    )
    posts = list(result.scalars().all())

    if not posts:
        return PerformancePatterns(total_posts=0)

    # Archetype performance
    archetype_map: dict[str, list[dict]] = {}
    for post in posts:
        task = await db.get(CoddeTask, post.task_id)
        if task and task.archetype:
            if task.archetype not in archetype_map:
                archetype_map[task.archetype] = []
            archetype_map[task.archetype].append(post.metrics)

    archetype_perf = []
    for archetype, metrics_list in archetype_map.items():
        impressions = [m.get("impressions", 0) for m in metrics_list]
        saves = [m.get("saves", 0) for m in metrics_list]
        comments = [m.get("comments", 0) for m in metrics_list]
        avg_imp = sum(impressions) / len(impressions) if impressions else 0
        avg_sav = sum(saves) / len(saves) if saves else 0
        avg_com = sum(comments) / len(comments) if comments else 0
        avg_rate = avg_sav / avg_imp if avg_imp > 0 else 0

        archetype_perf.append(ArchetypePerformance(
            archetype=archetype,
            avg_impressions=avg_imp,
            avg_saves=avg_sav,
            avg_save_rate=avg_rate,
            avg_comments=avg_com,
            post_count=len(metrics_list),
        ))

    # Overall
    all_impressions = [p.metrics.get("impressions", 0) for p in posts if p.metrics]
    all_saves = [p.metrics.get("saves", 0) for p in posts if p.metrics]
    avg_imp_total = sum(all_impressions) / len(all_impressions) if all_impressions else 0
    avg_save_total = sum(all_saves) / len(all_impressions) if all_impressions else 0

    return PerformancePatterns(
        archetype_performance=sorted(archetype_perf, key=lambda x: x.avg_save_rate, reverse=True),
        total_posts=len(posts),
        avg_save_rate=avg_save_total / avg_imp_total if avg_imp_total > 0 else 0,
        best_role=None,
        computed_at=datetime.utcnow(),
    )


# ── Composed Context for Agents ────────────────────────────────────────────────

async def compose_context(
    db: AsyncSession,
    stage: str,
    task_id: str | None = None,
    include_trending: list[dict] | None = None,
) -> ComposedContext:
    """Compose context window appropriate for the given lifecycle stage."""
    identity = await get_identity_memory(db)
    domains = await get_domains(db)
    recent = await get_recent_tasks(db, limit=5)

    context = ComposedContext(
        identity_memory=[
            {"type": e.type, "text": e.text, "tags": e.tags}
            for e in identity
        ],
        knowledge_domains=[
            {"id": d.id, "name": d.name, "tags": d.tags, "post_count": d.post_count}
            for d in domains
        ],
        recent_tasks=[
            {"id": t.id, "title": t.title, "stage": t.stage, "role": t.role, "domain": t.domain}
            for t in recent
            if t.id != task_id
        ],
        trending_context=include_trending or [],
    )

    # Add performance patterns for Discovery and Post-Mortem
    if stage in ("discovery", "post-mortem", "observatory"):
        context.performance_patterns = await compute_performance_patterns(db)

    return context
