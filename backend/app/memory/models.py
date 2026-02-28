"""
BroCoDDE — Memory Layer Pydantic Models
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ── Memory Entry ──────────────────────────────────────────────────────────────

class MemoryEntryCreate(BaseModel):
    type: str
    text: str
    tags: list[str] = Field(default_factory=list)


class MemoryEntryResponse(BaseModel):
    id: str
    type: str
    text: str
    tags: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Knowledge Domain ──────────────────────────────────────────────────────────

class KnowledgeDomainCreate(BaseModel):
    name: str
    color: str = "#D4A853"
    tags: list[str] = Field(default_factory=list)


class KnowledgeDomainResponse(BaseModel):
    id: str
    name: str
    color: str
    tags: list[str]
    post_count: int
    connections: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Performance Patterns ──────────────────────────────────────────────────────

class ArchetypePerformance(BaseModel):
    archetype: str
    avg_impressions: float
    avg_saves: float
    avg_save_rate: float
    avg_comments: float
    post_count: int


class DomainResonance(BaseModel):
    domain: str
    avg_engagement: float
    post_count: int


class PerformancePatterns(BaseModel):
    archetype_performance: list[ArchetypePerformance] = Field(default_factory=list)
    domain_resonance: list[DomainResonance] = Field(default_factory=list)
    top_intent: str | None = None
    best_role: str | None = None
    avg_save_rate: float = 0.0
    total_posts: int = 0
    computed_at: datetime | None = None


# ── Composed Context ──────────────────────────────────────────────────────────

class ComposedContext(BaseModel):
    identity_memory: list[dict[str, Any]] = Field(default_factory=list)
    knowledge_domains: list[dict[str, Any]] = Field(default_factory=list)
    performance_patterns: PerformancePatterns | None = None
    recent_tasks: list[dict[str, Any]] = Field(default_factory=list)
    trending_context: list[dict[str, Any]] = Field(default_factory=list)
    task_history: list[dict[str, Any]] = Field(default_factory=list)

    def to_prompt_text(self) -> str:
        """Render context as structured text for injection into agent prompts."""
        parts = []

        if self.identity_memory:
            parts.append("## User Identity")
            for entry in self.identity_memory:
                parts.append(f"- [{entry.get('type', 'Note')}] {entry.get('text', '')}")

        if self.knowledge_domains:
            parts.append("\n## Knowledge Domains")
            for domain in self.knowledge_domains:
                tags = ", ".join(domain.get("tags", []))
                parts.append(f"- {domain.get('name', '')} [{tags}] ({domain.get('post_count', 0)} posts)")

        if self.performance_patterns and self.performance_patterns.total_posts > 0:
            p = self.performance_patterns
            parts.append(f"\n## Performance Patterns")
            parts.append(f"- Total posts: {p.total_posts}, Avg save rate: {p.avg_save_rate:.1%}")
            if p.top_intent:
                parts.append(f"- Top intent: {p.top_intent}, Best role: {p.best_role}")

        if self.recent_tasks:
            parts.append("\n## Recent CoDDE Tasks")
            for task in self.recent_tasks[:5]:
                parts.append(f"- [{task.get('id')}] {task.get('title', 'Untitled')} ({task.get('stage')})")

        if self.trending_context:
            parts.append("\n## Trending Context")
            for item in self.trending_context[:3]:
                parts.append(f"- {item.get('title', '')}: {item.get('summary', '')}")

        return "\n".join(parts)
