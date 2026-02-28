"""
BroCoDDE — Agent Harness / Orchestrator
Routes each Workshop chat request to the correct agent based on CoDDE-task stage.
"""

import asyncio
from typing import AsyncIterator

from app.agents.analyst import build_analyst
from app.agents.interviewer import build_interviewer
from app.agents.shaper import build_shaper
from app.agents.strategist import build_strategist
from app.models.router import is_mock_mode

STAGE_AGENT_MAP = {
    "discovery":    "strategist",
    "extraction":   "interviewer",
    "structuring":  "shaper",
    "drafting":     "shaper",
    "vetting":      "shaper",
    "ready":        "shaper",
    "post-mortem":  "analyst",
    "observatory":  "analyst",
}


async def stream_chat(
    message: str,
    task_stage: str,
    task_id: str,
    role: str = "researcher",
    intent: str = "teach",
    user_id: str = "default_user",
    session_id: str | None = None,
    deep_critique: bool = False,
) -> AsyncIterator[str]:
    """
    Stream a chat response for the given CoDDE-task stage.
    Yields text chunks as they arrive.
    """
    if is_mock_mode():
        async for chunk in _mock_stream(task_stage, role):
            yield chunk
        return

    agent_name = STAGE_AGENT_MAP.get(task_stage, "shaper")
    session_id = session_id or f"{task_id}-{task_stage}"

    if agent_name == "strategist":
        agent = build_strategist(stage=task_stage, user_id=user_id, session_id=session_id)
    elif agent_name == "interviewer":
        agent = build_interviewer(role=role, user_id=user_id, session_id=session_id)
    elif agent_name == "analyst":
        agent = build_analyst(user_id=user_id, session_id=session_id)
    else:
        agent = build_shaper(mode=task_stage, user_id=user_id, session_id=session_id, deep_critique=deep_critique)

    try:
        # Run Agno agent asynchronously (supports async tools natively)
        async for event in agent.arun(message, user_id=user_id, stream=True):
            if hasattr(event, "content") and event.content:
                yield event.content
    except Exception as e:
        yield f"\n[Agent error: {e}]"


async def _mock_stream(stage: str, role: str) -> AsyncIterator[str]:
    """Yield mock streaming chunks when no API key is configured."""
    mock_messages: dict[str, list[str]] = {
        "discovery": [
            "**[MOCK — Discovery Brief]**\n\n",
            "Three angles worth exploring this session:\n\n",
            "**Option A:** A trending development in your primary domain.\n",
            "**Option B:** A cross-domain connection you're uniquely positioned to make.\n",
            "**Option C:** A field note from recent work that would resonate with practitioners.\n\n",
            "_Add `OPENROUTER_API_KEY` to `.env` for live agent responses._",
        ],
        "extraction": [
            f"**[MOCK — {role.title()} Interview]**\n\n",
            "What's the core insight you're trying to surface here?\n\n",
            "_Add `OPENROUTER_API_KEY` to `.env` for live agent responses._",
        ],
        "vetting": [
            "**[MOCK — Vetting Results]**\n\n",
            "✅ Opening strength: strong hook\n",
            "✅ No credential-stating detected\n",
            "⚠️ Engagement bait: ending question reads as bait — rewrite as declarative\n\n",
            "_Add `OPENROUTER_API_KEY` to `.env` for live agent responses._",
        ],
        "post-mortem": [
            "**[MOCK — Post-Mortem]**\n\n",
            "Share your 24hr metrics and I'll analyze them.\n",
            "_Add `OPENROUTER_API_KEY` to `.env` for live agent responses._",
        ],
    }
    for chunk in mock_messages.get(stage, ["[Mock response for this stage]\n"]):
        yield chunk
        await asyncio.sleep(0.02)  # Simulate streaming delay
