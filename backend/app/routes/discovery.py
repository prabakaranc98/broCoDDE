"""
BroCoDDE — Discovery Feed API
GET /discovery/feed  →  personalized card feed (3 sources)

Sources:
  HuggingFace  — daily papers, sorted by upvotes (>10 gate, fallback to top-N)
  HackerNews   — recent stories on user's top domains (search_by_date)
  Exa          — niche perspectives: substacks, blogs, underrated research angles

All three run concurrently. Cards are interleaved: paper, paper, discussion,
paper, paper, perspective, … so the feed always feels mixed.
"""

import asyncio
import logging
from typing import Any

import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import CoddeTask

log = logging.getLogger(__name__)
router = APIRouter()

_NICHE_DOMAINS = [
    "substack.com", "medium.com", "lesswrong.com", "gwern.net",
    "simonwillison.net", "eugeneyan.com", "lilianweng.github.io",
    "interconnects.ai", "thesequence.substack.com", "inference.substack.com",
    "bounded-regret.ghost.io", "transformer-circuits.pub",
]


class FeedCard(BaseModel):
    type: str          # "paper" | "discussion" | "perspective"
    source: str        # "HuggingFace" | "HackerNews" | "Exa"
    title: str
    summary: str
    url: str | None = None
    domain: str | None = None
    upvotes: int | None = None


@router.get("/feed", response_model=list[FeedCard])
async def get_discovery_feed(limit: int = 9, db: AsyncSession = Depends(get_db)):
    # Pull user's top domains from task history
    result = await db.execute(
        select(CoddeTask.domain, func.count(CoddeTask.domain).label("cnt"))
        .where(CoddeTask.domain.isnot(None))
        .group_by(CoddeTask.domain)
        .order_by(func.count(CoddeTask.domain).desc())
        .limit(3)
    )
    top_domains = [row.domain for row in result.fetchall()]
    if not top_domains:
        top_domains = ["machine learning", "artificial intelligence"]

    papers, discussions, perspectives = await asyncio.gather(
        _fetch_hf_papers(),
        _fetch_hn_stories(top_domains),
        _fetch_exa_perspectives(top_domains),
    )

    log.info(
        f"[feed] hf={len(papers)} hn={len(discussions)} exa={len(perspectives)} "
        f"domains={top_domains}"
    )

    # Interleave: 2 papers → 1 discussion → 2 papers → 1 perspective → repeat
    pattern = ["paper", "paper", "discussion", "paper", "paper", "perspective"]
    source_map = {"paper": papers, "discussion": discussions, "perspective": perspectives}
    indices = {"paper": 0, "discussion": 0, "perspective": 0}

    cards: list[FeedCard] = []
    for slot in pattern * 3:  # repeat pattern up to 3x
        if len(cards) >= limit:
            break
        pool = source_map[slot]
        idx = indices[slot]
        if idx < len(pool):
            cards.append(pool[idx])
            indices[slot] += 1

    return cards[:limit]


# ── Data fetchers ──────────────────────────────────────────────────────────────

async def _fetch_hf_papers() -> list[FeedCard]:
    """
    HF daily papers sorted by upvotes.
    Gate: >10 upvotes. Fallback: top-5 by upvotes if <3 pass the gate.
    """
    try:
        def _sync() -> list:
            from huggingface_hub import HfApi
            api = HfApi()
            all_papers = list(api.list_daily_papers(limit=50))
            all_papers.sort(key=lambda p: getattr(p, "upvotes", None) or 0, reverse=True)
            return all_papers

        all_papers = await asyncio.to_thread(_sync)

        filtered = [p for p in all_papers if (getattr(p, "upvotes", None) or 0) > 10]
        papers = filtered[:6] if len(filtered) >= 3 else all_papers[:5]

        cards = []
        for p in papers:
            paper_id = getattr(p, "id", "")
            title = getattr(p, "title", "").strip()
            upvotes = getattr(p, "upvotes", None) or 0
            summary = (
                getattr(p, "ai_summary", None)
                or getattr(p, "summary", "")
                or ""
            ).strip().replace("\n", " ")
            keywords = getattr(p, "ai_keywords", []) or []
            url = f"https://huggingface.co/papers/{paper_id}" if paper_id else None

            if not title:
                continue
            if len(summary) > 220:
                summary = summary[:217] + "…"

            cards.append(FeedCard(
                type="paper",
                source="HuggingFace",
                title=title,
                summary=summary or "No summary available.",
                url=url,
                domain=str(keywords[0]) if keywords else None,
                upvotes=upvotes,
            ))
        return cards

    except Exception as e:
        log.warning(f"[feed] HF papers error: {e}")
        return []


async def _fetch_hn_stories(domains: list[str]) -> list[FeedCard]:
    """Recent HN stories on user's domains (search_by_date, no points floor)."""
    keywords = " ".join(d.split(",")[0].strip() for d in domains[:2])
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(
                "https://hn.algolia.com/api/v1/search_by_date",
                params={"query": keywords, "tags": "story", "hitsPerPage": 8},
            )
            if not resp.is_success:
                log.warning(f"[feed] HN {resp.status_code}")
                return []

            cards = []
            for h in resp.json().get("hits", []):
                title = (h.get("title") or "").strip()
                if not title:
                    continue
                story_id = h.get("objectID", "")
                url = h.get("url") or f"https://news.ycombinator.com/item?id={story_id}"
                score = h.get("points") or 0
                comments = h.get("num_comments") or 0
                cards.append(FeedCard(
                    type="discussion",
                    source="HackerNews",
                    title=title,
                    summary=f"{score} pts · {comments} comments",
                    url=url,
                    upvotes=score,
                ))
            return cards

    except Exception as e:
        log.warning(f"[feed] HN error: {e}")
        return []


async def _fetch_exa_perspectives(domains: list[str]) -> list[FeedCard]:
    """
    Niche/underrated perspectives via Exa neural search.
    Targets substacks, blogs, and research angles not covered by HF/HN.
    Falls back to broader search if niche domains return nothing.
    """
    query = " ".join(d.split(",")[0].strip() for d in domains[:2])

    def _sync() -> list[FeedCard]:
        from app.config import settings
        from exa_py import Exa

        api_key = settings.exa_api_key
        if not api_key:
            return []

        exa = Exa(api_key=api_key)

        def _search(q: str, kwargs: dict[str, Any]) -> list:
            try:
                res = exa.search(
                    q,
                    type="auto",
                    num_results=4,
                    contents={"text": {"max_characters": 400}},
                    **kwargs,
                )
                return res.results or []
            except Exception:
                return []

        # Primary: niche domains
        results = _search(query, {"include_domains": _NICHE_DOMAINS})
        # Fallback: broader "underrated" framing
        if not results:
            results = _search(f"{query} underrated unique perspective", {})

        cards = []
        for r in results:
            title = (getattr(r, "title", None) or "").strip()
            url = getattr(r, "url", None)
            text = (getattr(r, "text", None) or "").strip().replace("\n", " ")
            if not title or not url:
                continue
            if len(text) > 200:
                text = text[:197] + "…"
            cards.append(FeedCard(
                type="perspective",
                source="Exa",
                title=title,
                summary=text or "Niche perspective — click to read.",
                url=url,
            ))
        return cards

    try:
        return await asyncio.to_thread(_sync)
    except Exception as e:
        log.warning(f"[feed] Exa perspectives error: {e}")
        return []
