"""
BroCoDDE — Context & Memory Layer Pydantic Models

Terminology note:
  source="user"  → context the human explicitly provided (expertise, voice, goals)
  source="agent" → context agents derived from conversations and post-mortems
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

# Valid lifecycle phases
LIFECYCLE_PHASES = [
    "discovery", "extraction", "structuring", "drafting",
    "vetting", "ready", "post-mortem",
]

# User-provided context types
USER_CONTEXT_TYPES = ["Experience", "Research", "Collaboration", "Philosophy", "Current", "Voice", "Goal"]

# Agent-derived context types
AGENT_CONTEXT_TYPES = ["Pattern", "Insight", "Hypothesis", "Finding", "Structural"]


# ── Context Entry (replaces MemoryEntry concept) ───────────────────────────────

class MemoryEntryCreate(BaseModel):
    type: str
    text: str
    tags: list[str] = Field(default_factory=list)
    source: Literal["user", "agent"] = "user"
    # lifecycle_phases: empty list = inject at all stages
    lifecycle_phases: list[str] = Field(default_factory=list)


class MemoryEntryResponse(BaseModel):
    id: str
    source: str
    type: str
    text: str
    tags: list[str]
    lifecycle_phases: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Agno Agent Memory (auto-written by MemoryManager) ────────────────────────

class AgnoMemoryResponse(BaseModel):
    id: str
    text: str
    topics: list[str]
    created_at: int       # Unix timestamp (seconds)
    updated_at: int | None
    evolved: bool         # True if updated meaningfully after creation


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
    # User-provided context: what the human explicitly told the system
    identity_memory: list[dict[str, Any]] = Field(default_factory=list)
    # Agent-derived context: what agents learned/extracted through conversations
    agent_context: list[dict[str, Any]] = Field(default_factory=list)
    knowledge_domains: list[dict[str, Any]] = Field(default_factory=list)
    performance_patterns: PerformancePatterns | None = None
    recent_tasks: list[dict[str, Any]] = Field(default_factory=list)
    trending_context: list[dict[str, Any]] = Field(default_factory=list)
    task_history: list[dict[str, Any]] = Field(default_factory=list)

    def to_prompt_text(self) -> str:
        """
        Render context as structured text for injection into agent system prompts.
        User-provided context and agent-derived context are rendered separately
        so agents understand the provenance of each piece of information.
        """
        parts = []

        if self.identity_memory:
            parts.append("## User Context (human-provided)")
            parts.append("_What the user has explicitly shared about themselves:_")
            for entry in self.identity_memory:
                parts.append(f"- [{entry.get('type', 'Note')}] {entry.get('text', '')}")

        if self.agent_context:
            parts.append("\n## Derived Context (agent-learned)")
            parts.append("_Patterns and insights extracted from past conversations and post-mortems:_")
            for entry in self.agent_context:
                tags_str = f" ({', '.join(entry.get('tags', []))})" if entry.get('tags') else ""
                parts.append(f"- [{entry.get('type', 'Insight')}]{tags_str} {entry.get('text', '')}")

        if self.knowledge_domains:
            parts.append("\n## Knowledge Domains")
            for domain in self.knowledge_domains:
                tags = ", ".join(domain.get("tags", []))
                parts.append(f"- {domain.get('name', '')} [{tags}] ({domain.get('post_count', 0)} posts)")

        if self.performance_patterns and self.performance_patterns.total_posts > 0:
            p = self.performance_patterns
            parts.append("\n## Performance Patterns")
            parts.append(f"- Total posts: {p.total_posts}, Avg save rate: {p.avg_save_rate:.1%}")
            for ap in p.archetype_performance[:3]:
                parts.append(f"  - {ap.archetype}: {ap.avg_save_rate:.1%} save rate ({ap.post_count} posts)")

        if self.recent_tasks:
            parts.append("\n## Recent CoDDE Tasks")
            for task in self.recent_tasks[:5]:
                parts.append(f"- [{task.get('id')}] {task.get('title', 'Untitled')} ({task.get('stage')})")

        if self.trending_context:
            parts.append("\n## Trending Context")
            for item in self.trending_context[:3]:
                parts.append(f"- {item.get('title', '')}: {item.get('summary', '')}")

        return "\n".join(parts)
