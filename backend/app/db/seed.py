"""
BroCoDDE — Demo Seed Data
Seeds the database with example series, domains, memory entries, and tasks
from the v0.4 system design spec if the database is empty.
"""

from datetime import datetime

from sqlalchemy import select

from app.db.database import AsyncSessionLocal
from app.db.models import CoddeTask, KnowledgeDomain, MemoryEntry, Series


async def seed_demo_data():
    """Seed demo data on first run."""
    async with AsyncSessionLocal() as session:
        # Check if already seeded
        result = await session.execute(select(Series).limit(1))
        if result.scalar_one_or_none():
            return

        # ── Series ────────────────────────────────────────────────────────────
        series_list = [
            Series(
                id="s-pracha-bridge",
                name="The Pracha Bridge",
                description="Connecting Tamil literature and ancient wisdom to modern ML and decision theory.",
                archetype="Bridge",
                icon="🌉",
                target_post_count=5,
            ),
            Series(
                id="s-causal-discovery",
                name="Causal Discovery in 4 Posts",
                description="From intuition to implementation — making causal inference accessible.",
                archetype="Micro-Learning",
                icon="🔗",
                target_post_count=4,
            ),
            Series(
                id="s-from-trenches",
                name="From the Trenches",
                description="War stories and hard lessons from production ML at Captain Fresh and beyond.",
                archetype="Field Note",
                icon="⚔️",
                target_post_count=6,
            ),
            Series(
                id="s-frontier-watch",
                name="Frontier Watch",
                description="Weekly curated developments at the frontier.",
                archetype="Annotated Shelf",
                icon="🔭",
                target_post_count=52,
            ),
            Series(
                id="s-visual-explainers",
                name="Visual Explainers",
                description="Complex concepts broken into visual, layered explanations.",
                archetype="Scientific Illustration",
                icon="🎨",
                target_post_count=8,
            ),
        ]
        for s in series_list:
            session.add(s)

        # ── Knowledge Domains ─────────────────────────────────────────────────
        domains = [
            KnowledgeDomain(
                name="Reinforcement Learning",
                color="#6366F1",
                tags=["RL", "Policy Gradient", "MARL", "Value Functions"],
                post_count=12,
            ),
            KnowledgeDomain(
                name="Causal Inference",
                color="#D4A853",
                tags=["DAGs", "Do-Calculus", "Counterfactuals", "SCM"],
                post_count=8,
            ),
            KnowledgeDomain(
                name="Decision Theory",
                color="#10B981",
                tags=["Game Theory", "Bayesian", "Rationality"],
                post_count=5,
            ),
            KnowledgeDomain(
                name="Tamil Philosophy",
                color="#F59E0B",
                tags=["Thirukural", "Sangam", "Ethics", "Wisdom"],
                post_count=4,
            ),
            KnowledgeDomain(
                name="LLM Systems",
                color="#EF4444",
                tags=["Agents", "RAG", "Fine-tuning", "Prompt Engineering"],
                post_count=9,
            ),
            KnowledgeDomain(
                name="Production ML",
                color="#8B5CF6",
                tags=["MLOps", "Deployment", "Monitoring", "Feature Stores"],
                post_count=7,
            ),
        ]
        for d in domains:
            session.add(d)

        # ── Identity Memory ───────────────────────────────────────────────────
        memory_entries = [
            MemoryEntry(
                type="Experience",
                text="Led ML platform and logistics optimization at Captain Fresh — 6+ years in production ML across different industries.",
                tags=["career", "ML", "Captain Fresh"],
            ),
            MemoryEntry(
                type="Research",
                text="PhD researcher at Columbia studying agentic decision sciences. Focus on LLM interpretability and causal reasoning under uncertainty.",
                tags=["Columbia", "PhD", "research"],
            ),
            MemoryEntry(
                type="Collaboration",
                text="Co-founder of CosmicAI — working on agentic systems for complex decision making.",
                tags=["CosmicAI", "startup", "AI"],
            ),
            MemoryEntry(
                type="Philosophy",
                text="Deep expertise in Tamil classical literature (Thirukural, Sangam poetry). Believes ancient wisdom systems encode sophisticated decision-making frameworks relevant to modern AI.",
                tags=["Tamil", "philosophy", "Thirukural"],
            ),
            MemoryEntry(
                type="Current",
                text="Building BroCoDDE as an IDE for engineered content development. Parallel focus: LLM negotiation agent interpretability framework.",
                tags=["BroCoDDE", "current", "projects"],
            ),
            MemoryEntry(
                type="Voice",
                text="Dense, precise, intellectually honest. No fluff, no engagement bait. Writes for inner-ring researchers and serious practitioners. Uses technical vocabulary naturally without over-explaining.",
                tags=["voice", "style", "writing"],
            ),
        ]
        for m in memory_entries:
            session.add(m)

        # ── Demo CoDDE Tasks ──────────────────────────────────────────────────
        demo_tasks = [
            CoddeTask(
                id="codde-20260228-001",
                title="The Do-Calculus as a Design Language for Agentic Systems",
                role="researcher",
                intent="teach",
                archetype="Framework Drop",
                domain="Causal Inference",
                series_id="s-causal-discovery",
                stage="vetting",
                extraction_transcript=[
                    {"role": "agent", "content": "What's the hypothesis you're testing with this post?"},
                    {"role": "user", "content": "That researchers building agentic systems are reinventing causal inference without naming it — and naming it would give them better tools."},
                    {"role": "agent", "content": "Strong thesis. What's the concrete example where Pearl's do-calculus would have changed a design decision you've seen made wrong?"},
                    {"role": "user", "content": "The RAG pipeline where the retrieval step was correlation-based but the generation step needed causal reasoning. Nobody saw the mismatch."},
                ],
                skeleton={
                    "hook": "Every RAG pipeline you've built has a causal reasoning assumption you never named.",
                    "insight": "Do-calculus as a design language — three operations: see, do, imagine",
                    "examples": ["RAG pipeline mismatch", "reward shaping as intervention", "tool use as action node"],
                    "landing": "Name the causal structure first. The architecture falls out of it.",
                },
                drafts=[
                    {"version": 1, "content": "Every agentic system you've built has a hidden causal graph...", "created_at": "2026-02-26T10:00:00Z"},
                    {"version": 2, "content": "The RAG pipeline you shipped last month has a problem nobody could name...", "created_at": "2026-02-27T14:00:00Z"},
                ],
                lint_results={
                    "rant_detection": {"pass": True, "notes": ""},
                    "fluff_detection": {"pass": True, "notes": ""},
                    "opening_strength": {"pass": True, "notes": "Strong cognitive tension in hook."},
                    "credential_stating": {"pass": True, "notes": ""},
                    "engagement_bait": {"pass": False, "notes": "Ending 'What causal assumptions are hiding in your systems?' reads as engagement bait. Rewrite as declarative."},
                    "micro_learning": {"pass": True, "notes": "Creator can articulate the do-calculus operations clearly."},
                },
                created_at=datetime(2026, 2, 26, 9, 0),
            ),
            CoddeTask(
                id="codde-20260225-002",
                title="What Thirukural Couplet 423 Taught Me About Multi-Agent Coordination",
                role="synthesizer",
                intent="connect",
                archetype="Bridge",
                domain="Tamil Philosophy",
                series_id="s-pracha-bridge",
                stage="ready",
                final_content="Couplet 423 of Thirukural: 'Act after careful thought; regret nothing after acting.' The Stoics said it. Kahneman studied it...",
                created_at=datetime(2026, 2, 25, 11, 0),
            ),
            CoddeTask(
                id="codde-20260220-003",
                title="Frontier Watch #3 — Week of Feb 20",
                role="cartographer",
                intent="curate",
                archetype="Annotated Shelf",
                domain="LLM Systems",
                series_id="s-frontier-watch",
                stage="post-mortem",
                final_content="This week at the frontier: three papers worth your attention...",
                published_at=datetime(2026, 2, 21, 9, 0),
                created_at=datetime(2026, 2, 20, 10, 0),
            ),
        ]
        for t in demo_tasks:
            session.add(t)

        await session.commit()
