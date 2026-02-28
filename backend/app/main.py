"""
BroCoDDE Backend — FastAPI + Agno AgentOS Entry Point

AgentOS mounts as the agentic runtime and control plane.
BroCoDDE domain routes (/tasks, /memory, /series, etc.) mount alongside it.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.database import create_tables
from app.db.seed import seed_demo_data
from app.routes import chat, memory, metrics, series, skills, tasks, voice


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: init SQLAlchemy tables, seed demo data, prime knowledge base."""
    await create_tables()
    await seed_demo_data()

    # Prime the skills knowledge base (non-blocking if no embedder key)
    try:
        from app.agents.knowledge import get_skills_knowledge
        get_skills_knowledge()
    except Exception:
        pass  # Graceful fallback: skills served via skill_load tool instead

    yield


app = FastAPI(
    title="BroCoDDE API",
    version="0.4.0",
    description="Content Development Life Cycle Engine — Agent Backend",
    lifespan=lifespan,
)

from app.logger import logging_middleware
from starlette.middleware.base import BaseHTTPMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # wide open for local dev — tighten in production
    allow_credentials=False,  # must be False when allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(BaseHTTPMiddleware, dispatch=logging_middleware)

# ── Mount AgentOS (Agno runtime + control plane + monitoring UI) ──────────────
try:
    from agno.app.agentapi import AgentAPI
    from app.agents.registry import get_agent_api

    agent_api: AgentAPI = get_agent_api()
    app.mount("/agentapi", agent_api.app)
except ImportError:
    pass  # Agno not yet installed; agents available via /tasks/:id/chat fallback

# ── BroCoDDE Domain Routes ────────────────────────────────────────────────────
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
app.include_router(chat.router, prefix="/tasks", tags=["chat"])
app.include_router(memory.router, prefix="/memory", tags=["memory"])
app.include_router(metrics.router, tags=["metrics"])
app.include_router(series.router, prefix="/series", tags=["series"])
app.include_router(skills.router, prefix="/skills", tags=["skills"])
app.include_router(voice.router, tags=["voice"])


@app.get("/health", tags=["system"])
async def health() -> dict:
    return {
        "status": "ok",
        "version": "0.4.0",
        "service": "BroCoDDE",
        "provider": settings.primary_provider,
        "mock_mode": not settings.has_any_ai_key,
    }
