"""
BroCoDDE — OpenRouter-based Model Router

All AI calls go through OpenRouter (https://openrouter.ai) using its
OpenAI-compatible API. Agno's OpenAIChat with a base_url override handles this.
"""

from agno.models.openai import OpenAIChat

from app.config import settings

# ── OpenRouter Model Registry ─────────────────────────────────────────────────
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_EXTRA_HEADERS = {
    "HTTP-Referer": "https://brocodde.prachalabs.com",
    "X-Title": "BroCoDDE",
}

OPENROUTER_MODELS: dict[int, dict[str, str]] = {
    1: {  # Tier 1 — Fast / Lightweight / Utility
        "primary": "openai/gpt-5.2-chat",
        "alt": "qwen/qwen3.5-plus",
    },
    2: {  # Tier 2 — Workhorse / Main Agents
        "primary": "anthropic/claude-sonnet-4.6",
        "alt": "openai/gpt-5.2",
    },
    3: {  # Tier 3 — Deep Reasoning / Strategic
        "primary": "anthropic/claude-opus-4.6",
        "alt": "openai/gpt-5.2-pro",
    },
}

# ── Task → Tier mapping (from spec §7.2 routing table) ───────────────────────
TASK_TIERS: dict[str, int] = {
    "discovery_brief": 3,
    "trending_fetch": 1,
    "extraction_interview": 2,
    "archetype_suggestion": 2,
    "skeleton_building": 2,
    "draft_qa": 2,
    "grammar_check": 1,
    "lint_analysis": 2,
    "deep_critique": 3,
    "post_mortem_analysis": 3,
    "weekly_retrospective": 3,
    "memory_summarization": 2,
    "memory_write": 1,
    "context_compression": 1,
}

# ── Pre-computed Task → Model ID mapping ──────────────────────────────────────
TASK_MODEL: dict[str, str] = {
    task: OPENROUTER_MODELS[tier]["primary"]
    for task, tier in TASK_TIERS.items()
}

# Override with alt model for high-volume cheap tasks
TASK_MODEL["context_compression"] = OPENROUTER_MODELS[1]["alt"]   # qwen3.5-plus
TASK_MODEL["memory_summarization"] = OPENROUTER_MODELS[1]["alt"]  # qwen3.5-plus


# ── Model Factory ─────────────────────────────────────────────────────────────

def get_model(tier: int = 2, use_alt: bool = False) -> OpenAIChat:
    """
    Return an Agno-compatible OpenAIChat configured for OpenRouter.
    Falls back to mock-friendly config if no key is set.
    """
    config = OPENROUTER_MODELS.get(tier, OPENROUTER_MODELS[2])
    model_id = config["alt"] if use_alt else config["primary"]

    # Allow env override per tier
    env_override = {
        1: settings.tier1_model,
        2: settings.tier2_model,
        3: settings.tier3_model,
    }.get(tier, "")

    # Use env override only if it's a full model path (contains "/")
    if "/" in env_override:
        model_id = env_override

    return OpenAIChat(
        id=model_id,
        api_key=settings.openrouter_api_key or "dummy-key",
        base_url=OPENROUTER_BASE_URL,
        default_headers=OPENROUTER_EXTRA_HEADERS,
    )


def get_model_for_task(task_name: str, use_alt: bool = False) -> OpenAIChat:
    """Return the configured model for a named task."""
    tier = TASK_TIERS.get(task_name, 2)
    model_id = TASK_MODEL.get(task_name, OPENROUTER_MODELS[tier]["primary"])

    if use_alt:
        model_id = OPENROUTER_MODELS[tier]["alt"]

    return OpenAIChat(
        id=model_id,
        api_key=settings.openrouter_api_key or "dummy-key",
        base_url=OPENROUTER_BASE_URL,
        default_headers=OPENROUTER_EXTRA_HEADERS,
    )


def is_mock_mode() -> bool:
    """True when no API key is configured — agents return mock responses."""
    return not bool(settings.openrouter_api_key)
