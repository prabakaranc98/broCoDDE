"""
BroCoDDE — Strategist Agent
Active during: Discovery (Tier 3) and Structuring (Tier 2).

Analytical, framework-grounded. Opens with a Discovery brief combining:
- User's identity and domain expertise (from MemoryManager)
- Trending topics (web_search tool)
- Performance patterns (compute_patterns tool)
- Content history (memory retrieval)

Loaded skills: content-discovery, audience-psychology, framework-library
"""

from agno.agent import Agent
from agno.memory import MemoryManager
from agno.models.anthropic import Claude
from agno.models.openai import OpenAIChat
from agno.tools.memory import MemoryTools

from app.agents.db import agno_db
from app.agents.knowledge import get_skills_knowledge
from app.agents.tools import (
    compute_patterns_tool,
    format_for_platform_tool,
    skill_list,
    skill_load,
    web_fetch_tool,
    web_search_tool,
)
from app.config import settings

DISCOVERY_INSTRUCTIONS = """
You are the Strategist for BroCoDDE — a Content Development Life Cycle engine.

Your role: Help the user identify what's worth creating in this session.

## Context Sources (always check before opening)
1. Search your memory for the user's identity, expertise, voice, and recent content history.
2. Use web_search to surface trending topics in the user's domains.
3. Use compute_patterns to pull performance data — what's working, what archetypes resonate.
4. Use skill_load("content-discovery") and skill_load("audience-psychology") before your first message.

## Discovery Brief Format
Open with a 3-option brief:
- Option A: A trending angle in a domain the user owns
- Option B: A connection nobody has articulated yet (cross-domain)
- Option C: Something the user has expertise in that the audience needs right now

Be direct. Make the options specific. Don't open with "I'd love to help."

## During Discovery
- Ask one sharp question at a time.
- Connect what the user says back to their content history and performance patterns.
- Name archetypes when you see them: Bridge, Field Note, Framework Drop, Micro-Learning, etc.
- Push back if the direction is too broad.
- When there's enough material, recommend advancing to Extraction.

## During Structuring (Tier 2 mode)
- Load skill_load("content-structuring") before suggesting structure.
- Suggest an archetype with rationale — one paragraph why this archetype for this topic.
- Build a skeleton: Hook, Core Insight, Key Points (max 3), Landing.
- Do NOT write prose. Structure only.
"""

STRUCTURING_INSTRUCTIONS = """
You are the Strategist in Structuring mode. The Extraction interview is complete.
Load skill_load("content-structuring") and skill_load("platform-linkedin") before responding.
Propose a content skeleton. One archetype, one hook, one landing. Tight and specific.
"""


def build_strategist(
    stage: str = "discovery",
    user_id: str = "default_user",
    session_id: str | None = None,
) -> Agent:
    """Build a Strategist agent calibrated for Discovery or Structuring."""

    # Tier 3 for Discovery, Tier 2 for Structuring
    is_discovery = stage == "discovery"
    model_id = settings.tier3_model if is_discovery else settings.tier2_model
    instructions = DISCOVERY_INSTRUCTIONS if is_discovery else STRUCTURING_INSTRUCTIONS

    def _make_model():
        return OpenAIChat(id=model_id, api_key=settings.openrouter_api_key or None, base_url="https://openrouter.ai/api/v1")

    memory_manager = MemoryManager(
        db=agno_db,
        model=OpenAIChat(id=settings.tier1_model, api_key=settings.openrouter_api_key or None, base_url="https://openrouter.ai/api/v1")
        if settings.has_any_ai_key
        else None,
        additional_instructions=(
            "Store insights about the user's expertise, voice, and content preferences. "
            "Tag memories with relevant domains and archetypes. "
            "Note what content angles worked and which didn't."
        ),
    )

    memory_tools = MemoryTools(db=agno_db)

    return Agent(
        name="strategist",
        model=_make_model(),
        instructions=instructions,
        tools=[
            memory_tools,
            web_search_tool,
            web_fetch_tool,
            skill_list,
            skill_load,
            compute_patterns_tool,
        ],
        knowledge=get_skills_knowledge(),
        search_knowledge=True,
        db=agno_db,
        memory_manager=memory_manager,
        update_memory_on_run=True,
        add_memories_to_context=True,
        user_id=user_id,
        session_id=session_id,
        markdown=True,
        stream=True,
    )
