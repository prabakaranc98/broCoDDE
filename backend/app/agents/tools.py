"""
BroCoDDE — Agent Tool Definitions
All tools registered as Pydantic AI / Agno tool functions.
"""

import json
from pathlib import Path
from typing import Any

import httpx

from app.config import settings

SKILLS_DIR = Path(__file__).parent.parent / "skills"


# ── Skill Tools ───────────────────────────────────────────────────────────────

async def skill_list() -> list[dict[str, str]]:
    """List all available skills with their names and descriptions."""
    skills = []
    for skill_dir in SKILLS_DIR.iterdir():
        skill_md = skill_dir / "SKILL.md"
        if skill_dir.is_dir() and skill_md.exists():
            content = skill_md.read_text()
            # Parse YAML frontmatter
            name = skill_dir.name
            description = ""
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    for line in parts[1].strip().splitlines():
                        if line.startswith("description:"):
                            description = line.replace("description:", "").strip()
                            break
                        elif line.startswith("name:"):
                            name = line.replace("name:", "").strip()
            skills.append({"name": name, "description": description, "dir": skill_dir.name})
    return skills


async def skill_load(skill_name: str) -> str:
    """Load the full content of a SKILL.md by skill name or directory name."""
    # Try exact directory match first
    skill_path = SKILLS_DIR / skill_name / "SKILL.md"
    if not skill_path.exists():
        # Try searching by name
        for skill_dir in SKILLS_DIR.iterdir():
            if skill_dir.is_dir() and skill_name.lower() in skill_dir.name.lower():
                skill_path = skill_dir / "SKILL.md"
                break

    if not skill_path.exists():
        return f"Skill '{skill_name}' not found."

    return skill_path.read_text()


async def skill_load_reference(skill_name: str, reference_name: str) -> str:
    """Load a reference file from a skill's references/ subdirectory."""
    ref_path = SKILLS_DIR / skill_name / "references" / f"{reference_name}.md"
    if not ref_path.exists():
        return f"Reference '{reference_name}' not found in skill '{skill_name}'."
    return ref_path.read_text()


# ── Memory Tools ──────────────────────────────────────────────────────────────

async def memory_read_tool(memory_type: str | None = None) -> str:
    """Read memory entries. Pass memory_type to filter (e.g. 'Experience', 'Research')."""
    from app.db.database import AsyncSessionLocal
    from app.db.models import MemoryEntry
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        query = select(MemoryEntry)
        if memory_type:
            query = query.where(MemoryEntry.type == memory_type)
        result = await db.execute(query.order_by(MemoryEntry.created_at.desc()))
        entries = result.scalars().all()

    return "\n".join([f"[{e.type}] {e.text}" for e in entries]) or "No memory entries found."


async def memory_write_tool(memory_type: str, text: str, tags: list[str] | None = None) -> str:
    """Write a new memory entry."""
    from app.db.database import AsyncSessionLocal
    from app.db.models import MemoryEntry

    async with AsyncSessionLocal() as db:
        entry = MemoryEntry(type=memory_type, text=text, tags=tags or [])
        db.add(entry)
        await db.commit()

    return f"Memory entry written: [{memory_type}] {text[:80]}..."


# ── Web Search Tool ────────────────────────────────────────────────────────────

async def web_search_tool(
    query: str,
    num_results: int = 8,
    category: str | None = None,
    include_domains: list[str] | None = None,
    max_age_hours: int | None = None,
) -> str:
    """
    Search the web using the Exa neural search API (exa-py SDK).

    Args:
        query: Natural-language search query.
        num_results: Number of results to return (default 8).
        category: Optional Exa category filter for targeted indexes:
            "research paper" — arxiv, paperswithcode, etc.
            "news"           — news articles
            "tweet"          — Twitter/X posts
            "company"        — company pages
        include_domains: Optional list of domains to restrict search to
            (e.g., ["arxiv.org", "github.com"]). Cannot combine with exclude.
        max_age_hours: Max content age. Omit for Exa default (recommended).

    Returns formatted string of results for agent consumption.
    """
    if not settings.exa_api_key:
        return (
            f"[Mock search — add EXA_API_KEY to .env]\n"
            f"- Trending: Example topic about '{query}'\n"
            f"- Paper: Recent work in this area\n"
            f"- Discussion: What practitioners are saying"
        )

    try:
        import asyncio
        from exa_py import Exa

        exa = Exa(api_key=settings.exa_api_key)

        # Build kwargs for search call
        search_kwargs: dict = {
            "query": query,
            "type": "auto",
            "num_results": num_results,
            "contents": {
                "text": {"max_characters": 10000},
            },
        }
        if category:
            search_kwargs["category"] = category
        if include_domains:
            search_kwargs["include_domains"] = include_domains
        if max_age_hours is not None:
            search_kwargs["contents"]["livecrawl_max_age"] = max_age_hours

        # exa-py is sync — run in thread pool
        results = await asyncio.to_thread(exa.search, **search_kwargs)

        if not results.results:
            return "No results found."

        lines = []
        for r in results.results:
            text_snippet = ""
            if hasattr(r, "text") and r.text:
                text_snippet = r.text[:400].strip().replace("\n", " ")
            lines.append(
                f"- **{r.title or 'Untitled'}**\n"
                f"  {text_snippet}\n"
                f"  {r.url}"
            )
        return "\n\n".join(lines)

    except Exception as e:
        return f"Exa search error: {e}"


async def web_fetch_tool(url: str) -> str:
    """Fetch and extract text content from a URL."""
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(url, timeout=15.0, headers={"User-Agent": "BroCoDDE/0.4"})
            # Basic HTML stripping
            text = response.text
            import re
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"\s+", " ", text).strip()
            return text[:3000] + ("..." if len(text) > 3000 else "")
    except Exception as e:
        return f"Fetch error: {e}"


# ── Lint Tool ─────────────────────────────────────────────────────────────────

async def lint_draft_tool(draft_content: str, task_id: str | None = None) -> dict[str, Any]:
    """
    Run AI-powered content vetting against a draft using the Tier 2 lint_analysis model.

    Evaluates six dimensions:
    - rant_detection: reactive, emotional, soapbox tone
    - fluff_detection: generic statements, filler, nothing uniquely yours
    - opening_strength: hook creates tension or curiosity in first line
    - credential_stating: explicit self-promotion (as a PhD, with 6 years...)
    - engagement_bait: "what do you think?", emoji overuse, motivational tone
    - micro_learning: does the content teach something specific and concrete?

    Returns structured JSON with pass/fail + specific line-level notes per check.
    Falls back to a clear error dict if the model call fails.
    """
    import json as _json

    from app.models.router import get_model_for_task

    # Load the vetting skill as context for the AI linter
    vetting_skill = await skill_load("content-vetting")

    system_prompt = f"""You are BroCoDDE's content linter. You apply specific quality gates to draft content.

Here are the exact rules you enforce:
{vetting_skill}

You return ONLY valid JSON. No prose before or after.
"""

    user_prompt = f"""Lint this draft and return a JSON object with exactly these six keys:
- rant_detection
- fluff_detection
- opening_strength
- credential_stating
- engagement_bait
- micro_learning

Each key maps to an object with:
- "pass": true or false
- "notes": "" if pass, or a specific 1-2 sentence note citing the exact phrase or line that fails

Also include a top-level "overall_pass": true only if ALL six checks pass.

Draft to lint:
---
{draft_content[:4000]}
---

Respond with ONLY the JSON object."""

    try:
        model = get_model_for_task("lint_analysis")
        # Use the model directly for a single structured call (not a full agent session)
        from openai import AsyncOpenAI

        client = AsyncOpenAI(
            api_key=model.api_key,
            base_url=model.base_url,
        )
        response = await client.chat.completions.create(
            model=model.id,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=800,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content or "{}"
        results: dict[str, Any] = _json.loads(raw)

        # Ensure overall_pass is present
        checks = ["rant_detection", "fluff_detection", "opening_strength",
                  "credential_stating", "engagement_bait", "micro_learning"]
        results["overall_pass"] = all(
            results.get(k, {}).get("pass", False) for k in checks
        )
        return results

    except Exception as e:
        # Return a clearly labelled error rather than silently wrong heuristics
        return {
            "error": f"Lint AI call failed: {e}",
            "overall_pass": False,
            "rant_detection": {"pass": False, "notes": "Lint unavailable — check API key."},
            "fluff_detection": {"pass": False, "notes": "Lint unavailable."},
            "opening_strength": {"pass": False, "notes": "Lint unavailable."},
            "credential_stating": {"pass": False, "notes": "Lint unavailable."},
            "engagement_bait": {"pass": False, "notes": "Lint unavailable."},
            "micro_learning": {"pass": False, "notes": "Lint unavailable."},
        }


# ── Format for Platform ────────────────────────────────────────────────────────

async def format_for_platform_tool(content: str, platform: str = "linkedin") -> str:
    """Format content for a specific platform (linkedin or twitter)."""
    if platform == "linkedin":
        # LinkedIn: max 3000 chars, line breaks every 3-4 sentences, no markdown
        lines = content.split("\n")
        formatted = []
        for line in lines:
            line = line.strip()
            if line.startswith("#"):
                line = line.lstrip("#").strip().upper()
            formatted.append(line)
        result = "\n\n".join([l for l in formatted if l])
        if len(result) > 3000:
            result = result[:2997] + "..."
        return result

    elif platform == "twitter":
        # Twitter/X: thread format, 280 chars per tweet
        sentences = content.replace("\n", " ").split(". ")
        tweets = []
        current = ""
        for s in sentences:
            if len(current) + len(s) + 2 < 260:
                current += s + ". "
            else:
                if current:
                    tweets.append(current.strip())
                current = s + ". "
        if current:
            tweets.append(current.strip())
        return "\n\n".join([f"{i+1}/{len(tweets)} {t}" for i, t in enumerate(tweets)])

    return content


# ── Export Tool ────────────────────────────────────────────────────────────────

async def export_task_tool(task_id: str, format: str = "markdown") -> str:
    """Export a CoDDE-task record as JSON or Markdown."""
    from app.db.database import AsyncSessionLocal
    from app.db.models import CoddeTask

    async with AsyncSessionLocal() as db:
        task = await db.get(CoddeTask, task_id)

    if not task:
        return f"Task {task_id} not found."

    if format == "json":
        return json.dumps({
            "id": task.id,
            "title": task.title,
            "role": task.role,
            "intent": task.intent,
            "archetype": task.archetype,
            "domain": task.domain,
            "stage": task.stage,
            "extraction_transcript": task.extraction_transcript,
            "skeleton": task.skeleton,
            "final_content": task.final_content,
        }, indent=2)
    else:
        lines = [
            f"# {task.title or task.id}",
            f"**ID:** {task.id}  **Stage:** {task.stage}",
            f"**Role:** {task.role}  **Intent:** {task.intent}",
            "",
        ]
        if task.skeleton:
            lines += ["## Skeleton", f"```json\n{json.dumps(task.skeleton, indent=2)}\n```", ""]
        if task.final_content:
            lines += ["## Final Content", task.final_content]
        return "\n".join(lines)


# ── Cross-Task Pattern Analysis ────────────────────────────────────────────────

async def compute_patterns_tool(limit: int = 20) -> str:
    """
    Analyse cross-task performance patterns from published post metrics.
    Used by the Analyst agent to identify what's driving save rates.

    Returns a structured Markdown summary of archetype, domain, and role patterns.
    """
    from app.db.database import AsyncSessionLocal
    from app.db.models import PostMetrics as PostMetricsModel
    from sqlalchemy import select, func

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(PostMetricsModel).order_by(PostMetricsModel.published_at.desc()).limit(limit)
        )
        posts = result.scalars().all()

    if not posts:
        return "No published post metrics yet. Complete a post-mortem first."

    # Aggregate by archetype
    by_archetype: dict[str, list[float]] = {}
    by_domain: dict[str, list[float]] = {}
    by_role: dict[str, list[float]] = {}

    for p in posts:
        rate = p.save_rate or 0.0
        if p.archetype:
            by_archetype.setdefault(p.archetype, []).append(rate)
        if p.domain:
            by_domain.setdefault(p.domain, []).append(rate)
        if p.role:
            by_role.setdefault(p.role, []).append(rate)

    def _top(d: dict[str, list[float]], n: int = 3) -> list[tuple[str, float]]:
        avgs = [(k, sum(v) / len(v)) for k, v in d.items()]
        return sorted(avgs, key=lambda x: x[1], reverse=True)[:n]

    lines = [
        f"## Cross-Task Performance Patterns ({len(posts)} posts)\n",
        "### By Archetype (save rate avg)",
    ]
    for name, avg in _top(by_archetype):
        lines.append(f"- **{name}**: {avg*100:.1f}%")

    lines += ["\n### By Domain"]
    for name, avg in _top(by_domain):
        lines.append(f"- **{name}**: {avg*100:.1f}%")

    lines += ["\n### By Role"]
    for name, avg in _top(by_role):
        lines.append(f"- **{name}**: {avg*100:.1f}%")

    overall_avg = sum(p.save_rate or 0.0 for p in posts) / len(posts)
    lines.append(f"\n**Overall avg save rate:** {overall_avg*100:.1f}%")

    return "\n".join(lines)

