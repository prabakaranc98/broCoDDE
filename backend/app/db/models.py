"""
BroCoDDE — SQLAlchemy ORM Models
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.utcnow()


class Series(Base):
    __tablename__ = "series"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    archetype: Mapped[str | None] = mapped_column(String(100))
    icon: Mapped[str | None] = mapped_column(String(50))
    target_post_count: Mapped[int] = mapped_column(default=5)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    tasks: Mapped[list["CoddeTask"]] = relationship("CoddeTask", back_populates="series")


class CoddeTask(Base):
    __tablename__ = "codde_tasks"

    id: Mapped[str] = mapped_column(String, primary_key=True)          # e.g. codde-20260228-001
    title: Mapped[str | None] = mapped_column(String(300))
    role: Mapped[str | None] = mapped_column(String(100))
    intent: Mapped[str | None] = mapped_column(String(100))
    archetype: Mapped[str | None] = mapped_column(String(100))
    domain: Mapped[str | None] = mapped_column(String(200))
    series_id: Mapped[str | None] = mapped_column(ForeignKey("series.id"), nullable=True)

    # Lifecycle stage
    stage: Mapped[str] = mapped_column(String(50), default="discovery")
    # discovery | extraction | structuring | drafting | vetting | ready | post-mortem

    # Content
    extraction_transcript: Mapped[list[dict]] = mapped_column(JSON, default=list)
    skeleton: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    drafts: Mapped[list[dict]] = mapped_column(JSON, default=list)
    lint_results: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    final_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    chat_history: Mapped[list[dict]] = mapped_column(JSON, default=list)

    # Timestamps
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    series: Mapped["Series | None"] = relationship("Series", back_populates="tasks")
    published_post: Mapped["PublishedPost | None"] = relationship(
        "PublishedPost", back_populates="task", uselist=False
    )


class MemoryEntry(Base):
    __tablename__ = "memory_entries"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    type: Mapped[str] = mapped_column(String(100))
    # Types: Experience | Research | Collaboration | Philosophy | Current | Goal | Voice
    text: Mapped[str] = mapped_column(Text)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class KnowledgeDomain(Base):
    __tablename__ = "knowledge_domains"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    color: Mapped[str] = mapped_column(String(20), default="#D4A853")
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    post_count: Mapped[int] = mapped_column(default=0)
    connections: Mapped[list[str]] = mapped_column(JSON, default=list)  # related domain IDs
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class PublishedPost(Base):
    __tablename__ = "published_posts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    task_id: Mapped[str] = mapped_column(ForeignKey("codde_tasks.id"))
    content: Mapped[str] = mapped_column(Text)
    platform: Mapped[str] = mapped_column(String(50), default="linkedin")
    metrics: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    # metrics: {impressions, saves, comments, dms, reposts, profile_visits}
    post_mortem_findings: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    task: Mapped["CoddeTask"] = relationship("CoddeTask", back_populates="published_post")
