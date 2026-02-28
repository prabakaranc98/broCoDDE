"""
BroCoDDE — Shaper Agent
Active during: Structuring, Drafting Q&A, and Vetting.

- Tier 2: General feedback, structural suggestions, draft Q&A
- Tier 3: Deep critique (escalates within same agent via higher-tier model)
- Tier 1: Grammar-only check (separate lightweight call)

Loaded skills: content-structuring, content-vetting, grammar-style, platform-linkedin
"""

from agno.agent import Agent
from agno.memory import MemoryManager
from agno.models.anthropic import Claude
from agno.models.openai import OpenAIChat

from app.agents.db import agno_db
from app.agents.knowledge import get_skills_knowledge
from app.agents.tools import (
    format_for_platform_tool,
    lint_draft_tool,
    skill_list,
    skill_load,
)
from app.config import settings

SHAPER_INSTRUCTIONS = """
You are the Shaper for BroCoDDE. You're active across Structuring, Drafting, and Vetting.

## Shaper Principles
- You understand the user's voice deeply from memory.
- You give structural feedback, not prose. You never write the post.
- You are a mirror for quality — honest, specific, not encouraging.

## During Structuring
1. Load skill_load("content-structuring") before responding.
2. Confirm the archetype selected in Discovery is right for the material.
3. Propose a tight skeleton: Hook line, Core insight (1 sentence), 3 key points, Landing.
4. Name things precisely. "Your hook creates cognitive tension" > "Your hook is good."

## During Drafting (Q&A mode)
- User is writing. You answer questions only. Do not volunteer feedback.
- Do NOT generate text. Do NOT complete sentences. Do NOT "improve" their writing.
- Valid: "That phrase means X, here's why it works or doesn't."
- Invalid: "Here's how I would write that section:"

## During Vetting
1. Load skill_load("content-vetting") and skill_load("grammar-style") first.
2. Run the lint_draft tool against the submitted draft.
3. Return the lint results with specific line-level feedback.
4. For deep critique, escalate to Tier 3 analysis of: structure coherence, insight density, opening strength.
5. Loop back to Drafting if lint fails. Be specific about what to fix, not that something is "off."
6. Grammar check is a separate lightweight call — flag grammar separately from structural feedback.

## During Platform Formatting
- Load skill_load("platform-linkedin") or platform-twitter based on target.
- Use format_for_platform tool to prepare the final draft.
"""


def build_shaper(
    mode: str = "vetting",   # structuring | drafting | vetting
    user_id: str = "default_user",
    session_id: str | None = None,
    deep_critique: bool = False,
) -> Agent:
    """Build a Shaper agent for the given mode and critique depth."""

    # Tier 3 for deep critique, Tier 2 for normal operation, Tier 1 for grammar-only
    model_id = (
        settings.tier3_model if deep_critique
        else settings.tier2_model
    )

    def _make_model():
        return OpenAIChat(id=model_id, api_key=settings.openrouter_api_key or None, base_url="https://openrouter.ai/api/v1")

    memory_manager = MemoryManager(
        db=agno_db,
        model=OpenAIChat(id=settings.tier1_model, api_key=settings.openrouter_api_key or None, base_url="https://openrouter.ai/api/v1")
        if settings.has_any_ai_key
        else None,
        additional_instructions=(
            "Capture what structural patterns work for this user's voice. "
            "Record which archetypes they're strong in, what kinds of hooks land, "
            "and recurring weaknesses to watch (fluff, credential-stating, etc.)."
        ),
    )

    return Agent(
        name="shaper",
        model=_make_model(),
        instructions=SHAPER_INSTRUCTIONS,
        tools=[skill_list, skill_load, lint_draft_tool, format_for_platform_tool],
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
