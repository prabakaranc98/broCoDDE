"""
BroCoDDE — Agno Knowledge Base
Skills repository served as inline context via the skill_load tool.
Vector RAG is skipped when no embedder key is available — which is always the
case with OpenRouter-only setups. Skills are loaded on-demand by agents via
the skill_load and skill_load_reference tools in tools.py.
"""

from pathlib import Path

SKILLS_DIR = Path(__file__).parent.parent / "skills"


def get_skills_knowledge():
    """
    Returns None — skills are loaded on-demand from the filesystem via the
    skill_load tool, which reads SKILL.md directly. This avoids requiring
    an OpenAI embedding key while still giving agents full skill access.
    """
    return None


def load_skill(skill_name: str) -> str | None:
    """Read a specific SKILL.md by directory name."""
    path = SKILLS_DIR / skill_name / "SKILL.md"
    if path.exists():
        return path.read_text()
    return None


def list_skills() -> list[str]:
    """Return all available skill directory names."""
    return sorted(d.name for d in SKILLS_DIR.iterdir() if d.is_dir() and (d / "SKILL.md").exists())
