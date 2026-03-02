"""
BroCoDDE — Content Discovery Toolkit

Unified Agno Toolkit for the Discovery stage. All signal sources in one place:

  Tool                  | Signal source       | Question answered
  ──────────────────────┼─────────────────────┼───────────────────────────────────────
  get_hf_daily_papers   | HuggingFace Hub     | What's hot in AI research today?
  search_hf_papers      | HuggingFace Hub     | What papers exist on topic X?
  search_hackernews     | HackerNews Algolia  | What are practitioners debating?
  search_news           | Exa (news)          | What's the industry coverage saying?
  search_research       | Exa (papers)        | What research exists on this angle?
  search_underrated     | Exa (niche)         | What angles are flying under the radar?

Discovery strategy: pair HF papers (academic frontier) + HN (practitioner sentiment)
to find the gap — that gap is where "Bridge" content lives.
Underrated search surfaces non-viral, under-covered angles worth owning early.
"""

import asyncio
from typing import Any

from agno.tools import Toolkit


class ContentDiscoveryToolkit(Toolkit):
    """
    Unified content discovery signals: HuggingFace Hub papers, HackerNews,
    and Exa topic/news/underrated search. Used by the Strategist during Discovery.
    """

    def __init__(self, hf_token: str | None = None, exa_api_key: str | None = None, **kwargs):
        # Store config before super().__init__ since it reads self.*
        self.hf_token = hf_token
        self._exa_api_key = exa_api_key

        super().__init__(
            name="content_discovery",
            tools=[
                self.get_hf_daily_papers,
                self.search_hf_papers,
                self.search_hackernews,
                self.search_news,
                self.search_research,
                self.search_underrated,
            ],
            **kwargs,
        )

    # ── HuggingFace Hub ───────────────────────────────────────────────────────

    def get_hf_daily_papers(
        self,
        date: str | None = None,
        limit: int = 5,
    ) -> str:
        """
        Fetch today's trending AI/ML papers from HuggingFace Hub daily papers feed.

        Shows what the research community is upvoting right now. Use at the start
        of Discovery to scan the academic frontier. Pair with search_hackernews to
        find the gap between research and practitioner understanding.

        Args:
            date: Date in YYYY-MM-DD format to get papers from a specific day.
                  Omit for today's papers.
            limit: Number of papers to return (1-10, default 5).

        Returns:
            Paper titles with upvote counts, AI keywords, summaries, and HF URLs.
        """
        try:
            from huggingface_hub import HfApi
        except ImportError:
            return "[ContentDiscovery] huggingface_hub not installed."

        try:
            api = HfApi(token=self.hf_token)
            call_kwargs: dict = {"limit": min(max(limit, 1), 10)}
            if date:
                call_kwargs["date"] = date

            papers = list(api.list_daily_papers(**call_kwargs))
            if not papers:
                return f"No HF daily papers found{' on ' + date if date else ' today'}."

            label = date or "Today"
            lines = [f"## HuggingFace Daily Papers — {label}\n"]
            for i, p in enumerate(papers[:limit], 1):
                paper_id = getattr(p, "id", "")
                title = getattr(p, "title", "No title")
                upvotes = getattr(p, "upvotes", 0)
                summary = getattr(p, "ai_summary", None) or getattr(p, "summary", "") or ""
                keywords = getattr(p, "ai_keywords", []) or []
                url = f"https://huggingface.co/papers/{paper_id}" if paper_id else ""

                if summary:
                    summary = summary[:280].strip().replace("\n", " ")

                lines.append(f"**{i}. {title}** ({upvotes} upvotes)")
                if keywords:
                    lines.append(f"   Keywords: {', '.join(str(k) for k in keywords[:5])}")
                if summary:
                    lines.append(f"   {summary}...")
                if url:
                    lines.append(f"   {url}")
                lines.append("")

            return "\n".join(lines)

        except Exception as e:
            return f"[ContentDiscovery] HF Hub error: {e}"

    def search_hf_papers(
        self,
        query: str,
        limit: int = 5,
    ) -> str:
        """
        Search HuggingFace Hub for papers on a specific topic or keyword.

        Use when the user wants to explore what research exists on a specific angle.
        Sorted by HF community upvotes — higher upvotes = more practitioner interest.

        Args:
            query: Keyword or topic (e.g. 'speculative decoding', 'vision language models',
                   'rlhf', 'mixture of experts', 'test-time compute').
            limit: Number of results to return (1-15, default 8).

        Returns:
            Matching papers with titles, upvotes, summaries, and HF URLs.
        """
        try:
            from huggingface_hub import HfApi
        except ImportError:
            return "[ContentDiscovery] huggingface_hub not installed."

        try:
            api = HfApi(token=self.hf_token)
            papers = list(api.list_papers(query=query))[:limit]

            if not papers:
                return f"No HF papers found for: '{query}'"

            lines = [f"## HuggingFace Papers — '{query}'\n"]
            for i, p in enumerate(papers, 1):
                paper_id = getattr(p, "id", "")
                title = getattr(p, "title", "No title")
                upvotes = getattr(p, "upvotes", 0)
                summary = getattr(p, "summary", "") or ""
                url = f"https://huggingface.co/papers/{paper_id}" if paper_id else ""

                if summary:
                    summary = summary[:230].strip().replace("\n", " ")

                lines.append(f"**{i}. {title}** ({upvotes} upvotes)")
                if summary:
                    lines.append(f"   {summary}...")
                if url:
                    lines.append(f"   {url}")
                lines.append("")

            return "\n".join(lines)

        except Exception as e:
            return f"[ContentDiscovery] HF search error: {e}"

    # ── HackerNews ────────────────────────────────────────────────────────────

    def search_hackernews(
        self,
        query: str,
        limit: int = 5,
    ) -> str:
        """
        Search HackerNews for stories and discussions on a topic.

        Use to gauge practitioner sentiment and energy around a topic.
        High score + many comments = practitioners care AND are debating.
        Low score + few comments = either ahead of its time or not resonating.

        Args:
            query: Topic to search (e.g. 'llm inference', 'vibe coding', 'ai agents').
            limit: Number of results to return (1-20, default 8).

        Returns:
            HN stories with titles, scores, comment counts, and URLs.
        """
        import urllib.request
        import urllib.parse
        import json as _json

        try:
            params = urllib.parse.urlencode({
                "query": query,
                "tags": "story",
                "hitsPerPage": min(limit, 20),
            })
            url = f"https://hn.algolia.com/api/v1/search?{params}"

            req = urllib.request.Request(url, headers={"User-Agent": "BroCoDDE/0.4"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = _json.loads(resp.read())

            hits = data.get("hits", [])
            if not hits:
                return f"No HackerNews stories found for: '{query}'"

            lines = [f"## HackerNews — '{query}'\n"]
            for i, h in enumerate(hits[:limit], 1):
                title = h.get("title", "No title")
                score = h.get("points", 0) or 0
                comments = h.get("num_comments", 0) or 0
                story_url = h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID', '')}"
                hn_url = f"https://news.ycombinator.com/item?id={h.get('objectID', '')}"

                lines.append(f"**{i}. {title}** ({score} pts, {comments} comments)")
                if story_url != hn_url:
                    lines.append(f"   Article: {story_url}")
                lines.append(f"   HN: {hn_url}")
                lines.append("")

            return "\n".join(lines)

        except Exception as e:
            return f"[ContentDiscovery] HackerNews error: {e}"

    # ── Exa Neural Search ────────────────────────────────────────────────────

    def _exa_search(self, query: str, num_results: int, category: str | None, include_domains: list[str] | None = None) -> str:
        """Internal: run Exa search synchronously (called from sync toolkit methods)."""
        from app.config import settings
        api_key = self._exa_api_key or settings.exa_api_key

        if not api_key:
            return (
                f"[ContentDiscovery] No EXA_API_KEY set — skipping Exa search for '{query}'.\n"
                f"Add EXA_API_KEY to .env to enable."
            )

        from exa_py import Exa
        exa = Exa(api_key=api_key)

        search_kwargs: dict[str, Any] = {
            "query": query,
            "type": "auto",
            "num_results": num_results,
            "contents": {"text": {"max_characters": 600}},
        }
        if category:
            search_kwargs["category"] = category
        if include_domains:
            search_kwargs["include_domains"] = include_domains

        results = exa.search(**search_kwargs)

        if not results.results:
            return f"No Exa results for: '{query}'"

        lines = []
        for r in results.results:
            text = ""
            if hasattr(r, "text") and r.text:
                text = r.text[:350].strip().replace("\n", " ")
            lines.append(f"- **{r.title or 'Untitled'}**")
            if text:
                lines.append(f"  {text}...")
            lines.append(f"  {r.url}")
        return "\n".join(lines)

    def search_news(
        self,
        query: str,
        limit: int = 4,
    ) -> str:
        """
        Search industry news and articles on a topic using Exa neural search.

        Use to find what mainstream tech media is covering on a subject.
        Cross-reference with search_underrated to spot the coverage gap.

        Args:
            query: Topic or angle to search news for.
            limit: Number of results to return (default 6).

        Returns:
            News articles with titles, excerpts, and URLs.
        """
        try:
            result = self._exa_search(query, num_results=limit, category="news")
            return f"## Industry News — '{query}'\n\n{result}"
        except Exception as e:
            return f"[ContentDiscovery] Exa news error: {e}"

    def search_research(
        self,
        query: str,
        limit: int = 4,
    ) -> str:
        """
        Search academic papers and research on a topic using Exa neural search.

        Use when you need depth behind a topic — what the research actually shows.
        Complements search_hf_papers (HF-only) with broader academic coverage.

        Args:
            query: Research topic or specific question.
            limit: Number of results to return (default 6).

        Returns:
            Research papers with titles, abstracts, and URLs.
        """
        try:
            result = self._exa_search(query, num_results=limit, category="research paper")
            return f"## Research — '{query}'\n\n{result}"
        except Exception as e:
            return f"[ContentDiscovery] Exa research error: {e}"

    def search_underrated(
        self,
        query: str,
        limit: int = 4,
    ) -> str:
        """
        Find underrated, niche, or under-covered angles on a topic using Exa.

        Unlike search_news (mainstream) or search_research (academic),
        this targets substacks, newsletters, personal blogs, and lesser-known
        publications — where original thinking often surfaces first.

        Use this to find angles the user can own before they go mainstream.

        Args:
            query: Topic or angle to find underrated content about.
            limit: Number of results to return (default 6).

        Returns:
            Niche articles and perspectives with titles, excerpts, and URLs.
        """
        try:
            # Target niche/non-mainstream publication domains
            niche_domains = [
                "substack.com",
                "medium.com",
                "lesswrong.com",
                "gwern.net",
                "simonwillison.net",
                "eugeneyan.com",
                "lilianweng.github.io",
                "interconnects.ai",
                "thesequence.substack.com",
                "inference.substack.com",
            ]
            result = self._exa_search(
                query,
                num_results=limit,
                category=None,
                include_domains=niche_domains,
            )
            # If niche search returns nothing (domains not matching), fall back to broad
            if "No Exa results" in result:
                result = self._exa_search(query + " underrated overlooked niche", num_results=limit, category=None)
            return f"## Underrated Angles — '{query}'\n\n{result}"
        except Exception as e:
            return f"[ContentDiscovery] Exa underrated error: {e}"
