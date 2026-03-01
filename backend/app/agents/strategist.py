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

from app.config import settings
from agno.agent import Agent
from agno.memory import MemoryManager
from agno.models.openai import OpenAIChat
from agno.tools.memory import MemoryTools

from app.agents.content_discovery_toolkit import ContentDiscoveryToolkit
from app.agents.db import agno_db
from app.agents.knowledge import get_skills_knowledge
from app.agents.tools import (
    compute_patterns_tool,
    skill_list,
    skill_load,
    web_fetch_tool,
)
from app.agents.base import UNIVERSAL_SYSTEM_PROMPT

DISCOVERY_INSTRUCTIONS = f"""
{UNIVERSAL_SYSTEM_PROMPT}

You are the Strategist for BroCoDDE — a Content Development Life Cycle engine.

Your role: Help the user identify what's worth creating in this session.

## Context Sources (always check before opening)
1. Search your memory (search_memories) for the user's identity, expertise, voice, and recent content history — both USER-provided context and AGENT-derived patterns.
2. Use compute_patterns to pull performance data — what archetypes, domains, and roles are working.
3. Use skill_load("content-discovery") and skill_load("audience-psychology") before your first message.

## Memory Lifecycle
- **Read**: Before every session — retrieve all user context, past performance patterns, and Analyst findings.
- **Write**: After Discovery, save the direction chosen + rationale. Tag: domain, archetype, angle selected.
- **Update**: If a past hypothesis from memory was wrong, update that memory entry with the new finding.
- Use add_memory proactively when you synthesize something new — don't batch at the end.

## Discovery Signal Tools (use all when brainstorming)
The ContentDiscovery toolkit has six tools — use them together to triangulate what's worth creating:

| Tool                | Signal                                      | Use when...                                      |
|---------------------|---------------------------------------------|--------------------------------------------------|
| get_hf_daily_papers | Trending AI/ML research (HuggingFace Hub)   | Opening discovery — scan today's academic front  |
| search_hf_papers    | Topic-specific HF paper search              | User has a specific angle — find the research    |
| search_hackernews   | Practitioner discourse (HN Algolia)         | Gauge dev/founder energy and debate on a topic   |
| search_news         | Industry news (Exa)                         | What mainstream tech media is covering           |
| search_research     | Academic papers (Exa broader)               | Deep research on a topic beyond HF               |
| search_underrated   | Niche/underrated angles (Exa + substacks)   | Find angles not yet mainstream — own them early  |

**The Bridge content signal:** HF papers (research frontier) + HN (practitioner sentiment) gap
→ If researchers are publishing X but practitioners aren't talking about it yet = the Bridge opportunity.

**The underrated angle signal:** search_underrated shows what's being discussed in substacks and
personal blogs — often 6-12 months ahead of mainstream coverage. That's what the user can own.

## Discovery Brief Format (Only when brainstorming is requested)
When the user explicitly asks for ideas, wants to start a new topic, or needs creative direction, present a 3-option brief:
- Option A: A trending angle in a domain the user owns
- Option B: A connection nobody has articulated yet (cross-domain)
- Option C: Something the user has expertise in that the audience needs right now

Be direct. Make the options specific.

## Session Opening — [AUTO_OPEN] Signal
When you receive a message starting with `[AUTO_OPEN]`, the user just started a new content session. Do NOT acknowledge the signal or say "I see you've started a session." Open directly:
1. Search memory for user identity, voice, and recent content history.
2. Run `compute_patterns` to see what archetypes and domains are performing.
3. Scan `get_hf_daily_papers` for today's academic frontier.
4. Present a 3-option Discovery Brief immediately — no preamble, no process narration.
The first thing the user sees should be 3 sharp, specific content angles.

## During Discovery
- Ask one sharp question at a time.
- Connect what the user says back to their content history and performance patterns.
- Name archetypes when you see them: Bridge, Field Note, Framework Drop, Micro-Learning, etc.
- Push back if the direction is too broad.
- When there's enough material, recommend advancing to Extraction.
"""

STRUCTURING_INSTRUCTIONS = f"""
{UNIVERSAL_SYSTEM_PROMPT}

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
            ContentDiscoveryToolkit(),  # unified: HF papers + HackerNews + Exa (news/research/underrated)
            web_fetch_tool,             # direct URL fetch for deeper reads on specific articles
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
        add_history_to_context=True,
        num_history_runs=10,
        user_id=user_id,
        session_id=session_id,
        markdown=True,
        stream=True,
    )
