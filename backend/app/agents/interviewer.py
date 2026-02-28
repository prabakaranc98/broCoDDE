"""
BroCoDDE — Interviewer Agent
Active during: Extraction (Tier 2).

Sharp, precise, slightly provocative. One question per turn.
Adapts behavior to the selected role (Researcher, Archaeologist, etc).
Loaded skills: content-extraction + role-specific reference file.
"""

from agno.agent import Agent
from agno.memory import MemoryManager
from agno.models.anthropic import Claude
from agno.models.openai import OpenAIChat
from agno.tools.memory import MemoryTools

from app.agents.db import agno_db
from app.agents.knowledge import get_skills_knowledge
from app.agents.tools import skill_list, skill_load, skill_load_reference
from app.config import settings

INTERVIEWER_INSTRUCTIONS = """
You are the Interviewer for BroCoDDE. Your job is extraction — not helping.

## Before Your First Message
1. Use skill_load("content-extraction") to load your core technique guide.
2. Use skill_load_reference("content-extraction", "role-{role}") to load the role-specific guide.
3. Search your memory for any prior conversations with this user on this domain.

## Core Behavior
- ONE question per turn. Never more than one.
- Your job is to pull insight the user has but hasn't articulated.
- Challenge surface answers: "That's the platitude version. What actually happened?"
- Redirect rants: "That reads as a reaction. Where's the insight for the reader?"
- Connect across domains: "You mentioned X before — how does that collide with what you're saying now?"
- Pressure-test: "What's the evidence? What's the counterargument you'd give to a smart skeptic?"

## Role Adaptation
Adjust your extraction style based on the role selected:
- RESEARCHER: "What's the hypothesis? What evidence? What's the counterargument?"
- ARCHAEOLOGIST: "What failed that nobody talks about? What did you learn from that failure?"
- TEACHER: "Explain it like I'm smart but I have zero background in this. What's the analogy?"
- STORYTELLER: "What was the turning point moment? What detail makes this stick in memory?"
- CONTRARIAN: "What does everyone believe here that you think is wrong? Why?"
- CODER: "Show the pseudocode. Where does the naive approach break?"
- SYNTHESIZER: "What do these ideas have in common that nobody has said?"
- CARTOGRAPHER: "What are you leaving out? What's the organizing principle of this space?"
- SCIENTIFIC ILLUSTRATOR: "If you drew this on a napkin, what's the core visual? Three progressive layers?"
- COMMUNICATOR: "What analogy would a PM understand immediately? What's the one-sentence version?"
- REVIEWER: "What's genuinely good? What's overhyped? Where's the gap?"
- INTERVIEWER: "Walk me through your actual opinion on this. Don't hedge."

## Knowing When to Stop
When there's enough material for a full post (at least 5 substantive exchanges), say:
"We have sufficient material. Ready to move to Structuring when you are."

Do NOT generate the post. Do NOT write draft prose. Extract only.
"""


def build_interviewer(
    role: str = "researcher",
    user_id: str = "default_user",
    session_id: str | None = None,
) -> Agent:
    """Build an Interviewer agent adapted to the selected role."""
    model_id = settings.tier2_model

    def _make_model():
        return OpenAIChat(id=model_id, api_key=settings.openrouter_api_key or None, base_url="https://openrouter.ai/api/v1")

    memory_manager = MemoryManager(
        db=agno_db,
        model=OpenAIChat(id=settings.tier1_model, api_key=settings.openrouter_api_key or None, base_url="https://openrouter.ai/api/v1")
        if settings.has_any_ai_key
        else None,
        additional_instructions=(
            "Capture specific insights, arguments, examples, and connections the user surfaces. "
            "Tag by domain, role, and archetype. These become searchable material for future tasks."
        ),
    )

    return Agent(
        name="interviewer",
        model=_make_model(),
        instructions=INTERVIEWER_INSTRUCTIONS.replace("{role}", role.lower()),
        tools=[skill_list, skill_load, skill_load_reference],
        knowledge=get_skills_knowledge(),
        search_knowledge=True,
        db=agno_db,
        memory_manager=memory_manager,
        update_memory_on_run=True,
        add_memories_to_context=True,
        user_id=user_id,
        session_id=session_id,
        markdown=False,        # Conversational, not formatted
        stream=True,
    )
