BroCoDDE — Complete System Design  
An IDE for Content Discovery, Development & Enablement  
Author: Prabakaran Chandran | Pracha Labs  
Version: 0.4 — Holistic Platform Design  
Date: February 28, 2026  

***

## 1. The Core Idea

BroCoDDE is a Content Development Life Cycle engine where every piece of content has a lifecycle, an identity, a lineage, and a feedback loop. The fundamental unit of work is the CoDDE-task — a uniquely identified content development cycle that carries its own context, memory, interactions, drafts, metadata, and post-mortem analysis. When the user clicks "+ New CoDDE-Task", they initiate a lifecycle, and the agent arrives fully loaded with the user's knowledge graph, prior performance patterns, current trending landscape, and the accumulated wisdom of every previous task.

The agent interviews, challenges, structures, and vets. It does not write the content. The user writes. Grammar checks and structural feedback are fine. Generating the post is not. The best content comes from genuine intellectual struggle — the agent creates conditions for that struggle, not bypass it.

***

## 2. The Content Development Life Cycle (CoDLC)

Every CoDDE-task moves through seven stages, visualized as a persistent lifecycle bar at the top of the Workshop view (see mockup 7):

- Discovery → Extraction → Structuring → Drafting → Vetting → Ready → Post-Mortem  

With a feedback loop:

- Findings from Post-Mortem feed back into Discovery.

### Stage 1: Discovery

Agent and user explore what's worth creating. Combines: user's knowledge and thinking (from context/memory), what the world is talking about (trending topics, papers), and what the audience needs (from performance data). Agent opens with a brief, user picks direction. Uses Tier 3 reasoning model.

### Stage 2: Extraction

The interview stage. Agent switches into chosen role and pulls insight through sharp questions. Challenges surface thinking, redirects ranting, connects across domains. Uses Tier 2 model.

### Stage 3: Structuring

Archetype selection and content skeleton. Hook, core insight, landing. Agent suggests structure, does not write prose. Uses Tier 2 model.

### Stage 4: Drafting

User writes. Human-only stage. Agent available for questions but does not generate text. This is where micro-learning happens. Uses Tier 2 model for Q&A.

### Stage 5: Vetting

Quality gates. Linter checks rant tone, fluff, opening strength, credential-stating, engagement bait, micro-learning verification. Specific feedback, loops back to drafting until cleared. Grammar uses Tier 1, lint analysis uses Tier 2, deep critique uses Tier 3.

### Stage 6: Ready

Draft queued for publishing with full CoDDE-task lineage (see mockup 3: Queue view showing draft with lint badges, metadata, series tag).

### Stage 7: Post-Mortem

User returns with 24hr metrics via chat. Agent analyzes, identifies patterns, stores findings. Feeds into future Discovery stages. Uses Tier 3 model.

***

## 3. CoDDE-Tasks

Each task carries: unique ID (e.g. `codde-20260228-002`), timestamp, selected role and intent, domain and archetype, full extraction transcript, structural skeleton, all draft versions, lint results, final published content, and post-mortem record.

The sidebar always shows the active task (ID, title, current stage) and recent tasks list with status indicators (see mockups 1–7: left sidebar with ACTIVE TASK card and RECENT list).

***

## 4. Roles and Intents

### Roles

The role selection is the first step when creating a new CoDDE-task. Each role is presented as a card with an icon, name, and one-line description (see mockup 1: Role selection grid, ROLE → INTENT → BEGIN flow).

- Researcher — Methodological depth, hypothesis-driven. "What's the hypothesis? What evidence? What's the counterargument?"
- Reviewer — Critical evaluation of papers, tools, approaches. "What's genuinely good? What's overhyped?"
- Archaeologist — Dig into past experience for buried insights. "What happened that nobody talks about? What failed?"
- Teacher — Explain deeply understood concepts clearly. Agent plays the student. "Explain like I have a CS degree but no RL background."
- Interviewer — Structured interview drawing out perspectives. Sharp, specific questions about opinions and experiences.
- Coder — Technical implementation, algorithms, code insights. "Show the pseudocode. Where does the naive approach break?"
- Synthesizer — Unify multiple ideas into a perspective. "What do these three papers have in common nobody has articulated?"
- Contrarian — Position against prevailing consensus. Agent plays devil's advocate from the other side.
- Storyteller — Narrate experiences and journeys. "What was the turning point? What detail makes this stick?"
- Cartographer — Map landscapes, fields, problem spaces. "What are you leaving out? What's the organizing principle?"
- Scientific Illustrator — Design visual and conceptual accessibility. "If you drew this on a napkin, what would it look like? What's the core visual metaphor? Can we decompose into three progressive layers?" Pushes for information hierarchy, suggests visual structures (flowcharts, matrices, progressive-reveal diagrams). User creates the actual illustration.
- Communicator — Translation from expert jargon to accessible framing. "What analogy would you reach for? What's the everyday experience that mirrors this? What's the one-sentence version a PM would repeat?" Bridges academic understanding to audience frame of reference.

### Intents

Selected after role, second step in the flow:

- Teach — Help audience learn. Metric target: saves & reshares.
- Connect — Draw unexpected connections. Metric target: comment quality, inner-ring DMs.
- Curate — Be the best resource collection. Metric target: saves, follower growth.
- Provoke — Shift how people think. Metric target: comments, profile visits.
- Demonstrate — Show competence through real work. Metric target: inner-ring engagement.
- Bridge — Make cross-domain expertise visible. Metric target: memorability, reshares.

***

## 5. Content Series

The Series view shows active series with progress bars, post count, archetype badge, and last activity date. Each series is expandable to show its constituent CoDDE-tasks and narrative arc (see mockup 6: Series view).

Example series:

- The Pracha Bridge — Connecting Tamil literature and ancient wisdom to modern ML and decision theory. Archetype: Bridge. Recurring signature format.
- Causal Discovery in 4 Posts — From intuition to implementation — making causal inference accessible. Archetype: Micro-Learning/Teacher series.
- From the Trenches — War stories and hard lessons from production ML at Captain Fresh and beyond. Archetype: Field Note.
- Frontier Watch — Weekly curated developments at the frontier. Archetype: Annotated Shelf.
- Learning in Public — Current studies and research in progress at Columbia and Cosmicai.
- Visual Explainers — Complex concepts broken into visual, layered explanations. Uses Scientific Illustrator role.
- Frameworks Applied — One framework per post applied to ML/AI. Archetype: Framework Drop.

***

## 6. Agent Skills Repository

Following the Anthropic Agent Skills standard (agentskills.io) and the `pydantic-ai-skills` library pattern, BroCoDDE's agents use a skills repository — filesystem-based `SKILL.md` files loaded on-demand via progressive disclosure. The agent sees skill names and descriptions at startup, and loads full instructions only when the lifecycle stage or user request matches a skill's domain. This keeps the context lean while providing deep expertise when needed. [github](https://github.com/DougTrajano/pydantic-ai-skills)

### Skills Directory

```text
backend/app/skills/
├── content-discovery/
│   └── SKILL.md              # Trending analysis, angle suggestion, Discovery brief generation
├── content-extraction/
│   ├── SKILL.md              # Core interview techniques, role-adaptive behavior
│   └── references/
│       ├── role-researcher.md
│       ├── role-archaeologist.md
│       ├── role-illustrator.md
│       ├── role-communicator.md
│       └── role-contrarian.md
├── content-structuring/
│   ├── SKILL.md              # Archetype formats, skeleton building
│   └── references/
│       └── archetype-formats.md
├── content-vetting/
│   ├── SKILL.md              # Lint checks, quality gates
│   └── references/
│       └── lint-rules.md     # Detailed rant/fluff/hook/cred/bait rules
├── post-mortem-analysis/
│   └── SKILL.md              # Metric analysis, pattern recognition, recommendations
├── audience-psychology/
│   ├── SKILL.md              # LinkedIn/Twitter audience behavior models
│   └── references/
│       ├── us-professional.md
│       ├── india-student.md
│       └── inner-ring-researcher.md
├── framework-library/
│   ├── SKILL.md              # How to ground content decisions in frameworks
│   └── references/
│       ├── 48-laws.md
│       ├── cialdini.md
│       ├── made-to-stick.md
│       └── design-thinking.md
├── platform-linkedin/
│   └── SKILL.md              # LinkedIn formatting, algorithm, character limits
├── platform-twitter/
│   └── SKILL.md              # Twitter/X thread structure, culture
├── visual-explanation/
│   └── SKILL.md              # Diagram types, visual metaphors, info hierarchy
├── communication-bridge/
│   └── SKILL.md              # Jargon-to-accessible translation techniques
├── grammar-style/
│   └── SKILL.md              # Grammar checking, Pracha's voice guide, tone rules
└── series-management/
    └── SKILL.md              # Series continuity, narrative arcs, gap identification
```

### Example SKILL.md

```markdown
---
name: content-vetting
description: >
  Run quality gates on content drafts. Checks for rant tone, fluff, opening
  strength, credential-stating, engagement bait, and micro-learning verification.
  Use when a CoDDE-task is in the Vetting stage.
---
# Content Vetting Skill

## When to Use
Activate when a CoDDE-task enters the Vetting stage and a draft needs quality
assessment before moving to Ready.

## Lint Checks

### Rant Detection
Flag content that is reactive, emotional, or soapbox-like. Redirect:
"This reads as a reaction. Where's the learning for the reader?"

### Fluff Detection
Flag generic statements that could appear in anyone's post. Push for
specificity: "What detail here is uniquely yours?"

### Opening Strength
First line must create curiosity or cognitive tension. Flag weak hooks:
"Your opening doesn't create tension until line 3."

### Credential Stating
Catch explicit credential-stating like "As a Columbia student..." or
"With 6+ years of experience..." Suggest natural embedding instead.

### Engagement Bait
Flag "What do you think?" endings, emoji overuse, motivational tone,
"I'm excited to announce" patterns.

### Micro-Learning Verification
Ask the creator: "What did YOU learn from making this?" If nothing —
back to Extraction.

## Output Format
Return structured JSON with pass/fail per check and specific notes.
```

### Skill Loading per Lifecycle Stage

- During Discovery, the harness loads: `content-discovery`, `audience-psychology`, `framework-library`.
- During Extraction with a Scientific Illustrator role, it loads: `content-extraction` + `visual-explanation` + the role-specific reference file.
- During Vetting, it loads: `content-vetting` + `grammar-style` + `platform-linkedin`.

This progressive disclosure is handled by the harness, not the agents. [skillsllm](https://skillsllm.com/skill/pydantic-ai-skills)

***

## 7. AI Model Architecture, Routing, and Agent OS

BroCoDDE runs on top of Agno’s AgentOS runtime, which provides the production backend for agentic systems while exposing a FastAPI-compatible surface. Agno handles agent orchestration, session management, and tool wiring, and BroCoDDE supplies the domain-specific lifecycle logic (CoDDE-tasks, roles, intents, and skills). [docs.agno](https://docs.agno.com/agent-os/overview)

### 7.1. Model Tiers

- **Tier 1: Fast / Lightweight** — Grammar checks, text formatting, memory writes, simple classification, context compression. Models: `claude-haiku-4-5-20251001`, `gpt-4o-mini`, or local via Ollama (e.g. `llama-3.2-3b`, `phi-3-mini`). Priority: speed and cost. Under 2 seconds. Frequent calls.
- **Tier 2: Balanced / Workhorse** — Extraction interviews, shaping feedback, structuring, general lint checks, draft Q&A. Models: `claude-sonnet-4-5-20250929`, `gpt-4o`. Priority: quality conversation at reasonable cost. Majority of daily calls.
- **Tier 3: Reasoning / Deep** — Discovery briefs, deep critique, post-mortem analysis, pattern recognition, weekly retrospectives, strategic recommendations. Models: `claude-opus-4-5-20250929`, `o3-mini`, `deepseek-r1` (for budget reasoning). Priority: depth of insight. Few calls per day, high-stakes quality. [ai.pydantic](https://ai.pydantic.dev/toolsets/)

### 7.2. Routing Table

```text
Task                        Agent          Tier      Model Example
─────────────────────────────────────────────────────────────────
Discovery brief             Strategist     Tier 3    claude-opus-4-5
Trending topic fetch        Tooling        Tier 1    + web search API
Extraction interview        Interviewer    Tier 2    claude-sonnet-4-5
Archetype suggestion        Shaper         Tier 2    claude-sonnet-4-5
Skeleton building           Shaper         Tier 2    claude-sonnet-4-5
Draft Q&A                   Shaper         Tier 2    gpt-4o
Grammar check               Linter         Tier 1    claude-haiku-4-5
Lint (rant/fluff/hook)      Shaper         Tier 2    claude-sonnet-4-5
Deep critique               Shaper         Tier 3    claude-opus-4-5
Post-mortem analysis        Analyst        Tier 3    claude-opus-4-5
Weekly retrospective        Analyst        Tier 3    claude-opus-4-5
Memory summarization        Harness        Tier 2    claude-sonnet-4-5
Memory write                Harness        Tier 1    claude-haiku-4-5
Context compression         Harness        Tier 1    claude-haiku-4-5
Voice transcription         Whisper        External  whisper-1
Web search                  Tooling        External  search API
```

### 7.3. AgentOS Integration

- AgentOS runs as the agentic runtime and control plane, embedding BroCoDDE’s agents as named services inside an Agno AgentOS instance. [docs.agno](https://docs.agno.com/introduction)
- The BroCoDDE backend mounts AgentOS into the same FastAPI app, exposing a unified API to the Next.js frontend. [github](https://github.com/agno-agi/agno)
- Each BroCoDDE agent (Strategist, Interviewer, Shaper, Analyst) is implemented as an Agno agent with bound tools and tier/model configuration mapped to Agno’s model abstraction layer. [docs.agno](https://docs.agno.com/agent-os/overview)
- AgentOS’s control plane UI can be used in development and production to monitor BroCoDDE’s agents, conversations, and errors. [spacesail.mintlify](https://spacesail.mintlify.app/agent-os/introduction)

### 7.4. Memory and Knowledge via Agno

Agno provides built-in agentic memory with support for automatic capture, retrieval, and summarization of user facts and session history. BroCoDDE maps its six memory layers onto Agno’s memory primitives: [docs.agno](https://docs.agno.com/memory/overview)

- Layer 1: Identity Memory — long-term user memory storing editable identity and voice facts keyed by user ID. [youtube](https://www.youtube.com/watch?v=0P6ydQJXtuM)
- Layer 2: Knowledge Graph — BroCoDDE’s domain tables surfaced to agents through Agno’s knowledge interfaces. [docs.agno](https://docs.agno.com/introduction)
- Layer 3: Content History — AgentOS session history plus `codde_tasks` and `published_posts` records, with high-signal summaries for each user and task. [github](https://github.com/agno-agi/agno)
- Layer 4: Performance Patterns — stored in BroCoDDE’s DB and injected into agents as “knowledge” objects via Agno’s context APIs when relevant. [docs.agno](https://docs.agno.com/memory/overview)
- Layer 5: Session Context — session-scoped memory and automatic chat summaries keep context windows compact. [youtube](https://www.youtube.com/watch?v=0P6ydQJXtuM)
- Layer 6: Trending Context — fetched via `web_search` and stored as ephemeral Agno memories or cached KB entries attached to Discovery sessions. [docs.agno](https://docs.agno.com/agent-os/overview)

Agentic memory is enabled so agents can decide when to write or update memories, while BroCoDDE still defines explicit tools like `memory_read` and `memory_write` for critical lifecycle events. [docs.agno](https://docs.agno.com/memory/overview)

### 7.5. Skills, Tools, and Workflows with Agno

Agno’s framework layer is used to define BroCoDDE’s agents, tools, and multi-step workflows. [docs.agno](https://docs.agno.com/introduction)

- Each BroCoDDE skill is packaged as a filesystem `SKILL.md` and registered as an Agno tool bundle; skills are loaded on demand using progressive disclosure. [github](https://github.com/DougTrajano/pydantic-ai-skills)
- Existing tools (`memory_read`, `memory_write`, `skill_list`, `skill_load`, `web_search`, `web_fetch`, `transcribe_audio`, `lint_draft`, `format_for_platform`, `export_task`, `compute_patterns`) are implemented as Agno tools and attached to agents via AgentOS configuration. [github](https://github.com/agno-agi/agno)
- Lifecycle flows are represented as Agno workflows or teams, enabling BroCoDDE to orchestrate handoffs between Strategist, Interviewer, Shaper, and Analyst while AgentOS manages execution and logging. [docs.agno](https://docs.agno.com/agent-os/overview)

### 7.6. Provider Flexibility

The harness uses a provider-agnostic interface via Agno and Pydantic AI's model-agnostic layer. Users configure API keys per provider and assign providers to tiers. Mix Claude Opus for Tier 3, GPT-4o for Tier 2, local Llama via Ollama for Tier 1. Providers are swappable without changing agent logic. [ai.pydantic](https://ai.pydantic.dev/toolsets/)

***

## 8. Tooling Layer

Core Agent Tools (registered as Agno tools / Pydantic AI tools):

- `memory_read` — Read from any memory layer. Used by all agents to access context.
- `memory_write` — Write observations back. Analyst writes performance patterns, Interviewer updates knowledge graph when discovering new domain connections.
- `skill_list` — List available skills with names and descriptions. Used at session start.
- `skill_load` — Load full `SKILL.md` content. Triggered by lifecycle stage transitions.
- `web_search` — Search for trending topics, recent papers, platform conversations. Used during Discovery. Implementation: Brave Search API or Serper API.
- `web_fetch` — Fetch and extract content from a URL. Read papers, blog posts, articles.
- `transcribe_audio` — Takes audio and returns text. Server-side: OpenAI Whisper API (`whisper-1`).
- `lint_draft` — Runs content-vetting skill against a draft, returns structured pass/fail results.
- `format_for_platform` — Format content for LinkedIn or Twitter. Handles character limits, line breaks, platform conventions. Uses Tier 1 model.
- `export_task` — Export CoDDE-task record as JSON or Markdown.
- `compute_patterns` — Run pattern computation across published posts. Updates performance patterns layer. [ai.pydantic](https://ai.pydantic.dev/toolsets/)

***

## 9. Memory and Context Management

### Six Memory Layers

1. **Layer 1: Identity Memory** — Persistent, user-editable. Who the user is: experience, research, interests, voice, goals. Directly editable in the Context view (see mockup 5: Identity Memory entries with type badges and edit icons).
2. **Layer 2: Knowledge Graph** — Persistent, growing. Domains with colored indicators, tags, and post counts (see mockup 5: Domain cards like "Reinforcement Learning" with tags `[RL, Policy Gradient, MARL]` and "12 posts"). Tracks explored connections and untapped edges.
3. **Layer 3: Content History** — Persistent, append-only. Every CoDDE-task record.
4. **Layer 4: Performance Patterns** — Computed after each post-mortem. Archetype performance, domain resonance by audience ring, opening style effectiveness, optimal timing.
5. **Layer 5: Session Context** — Ephemeral, per CoDDE-task. Current conversation, draft state, lint results.
6. **Layer 6: Trending Context** — Ephemeral, refreshed per session. Current landscape, recent papers. [strapi](https://strapi.io/blog/content-lifecycle-management)

### Context Injection

The harness composes the context window per agent call. Selective, not exhaustive. The Workshop view's right panel shows which context layers are loaded (see mockup 7: "CONTEXT LOADED" panel showing Identity Memory, Knowledge Graph, Performance Patterns, Trending Context with green indicators).

***

## 10. I/O and Interaction

### Text Input (Primary)

Chat-based for all lifecycle stages. Workshop view shows the chat with the active agent, input at the bottom with placeholder "Reply to the Researcher..." (see mockup 7).

### Voice Input (Quick Capture)

Speech-to-text input for fast extraction. User speaks, BroCoDDE transcribes to text, text enters normal chat flow. Not real-time bidirectional voice conversation — it's a mic button next to the text input that captures speech and converts.

Implementation: Browser-side Web Speech API for real-time transcription. Server-side Whisper API for uploaded recordings or when higher accuracy is needed. Transcribed text is displayed for review before sending. [linkedin](https://www.linkedin.com/pulse/server-sent-events-sse-fastapi-manikandan-parasuraman-q07ff)

### File Uploads

Context view supports "Upload Context" button (see mockup 5). Accepts transcripts (`txt`, `md`), documents (`pdf`), images (`png`, `jpg`). Processed and added to memory.

### Metrics via Chat

User reports metrics conversationally in Post-Mortem stage: "Got 1,200 impressions, 45 saves, 12 comments." Agent parses and stores.

***

## 11. Agent Architecture

### Four Agents (Agno / Pydantic AI Agent instances)

- **Interviewer** — Active during Extraction. Sharp, precise, slightly provocative. One question at a time. Adapts style to selected role. Uses Tier 2. Loads `content-extraction` skill + role-specific reference.
- **Strategist** — Active during Discovery and Structuring. Analytical, framework-grounded. Suggests themes and angles based on trending data, audience patterns, content history. Uses Tier 3 for Discovery, Tier 2 for Structuring. Loads `content-discovery`, `audience-psychology`, `framework-library` skills.
- **Shaper** — Active during Structuring, Drafting, and Vetting. Understands user's voice deeply. Provides structural suggestions, opening alternatives, refinement feedback. Runs the linter. Uses Tier 2 for feedback, Tier 3 for deep critique, Tier 1 for grammar. Loads `content-structuring`, `content-vetting`, `grammar-style`, `platform-linkedin` skills.
- **Analyst** — Active during Post-Mortem and Observatory. Data-driven, honest. Analyzes metrics in context. Identifies cross-post patterns. Provides specific next-cycle recommendations. Uses Tier 3 exclusively. Loads `post-mortem-analysis` skill.

### Context Injection per Agent

Every call includes composed context appropriate to agent and stage. The harness handles composition: Interviewer gets identity memory + selected role/domain + prior tasks on same topic. Strategist gets performance patterns + content history + trending context. Analyst gets full metrics history + current task lineage. [youtube](https://www.youtube.com/watch?v=0P6ydQJXtuM)

***

## 12. Infrastructure and Tech Stack

### Backend: Python (FastAPI + Agno AgentOS + Pydantic AI)

- FastAPI for the API layer — async, fast, typed, great for streaming responses via Server-Sent Events (SSE).
- Agno AgentOS as the agent runtime and control plane. [spacesail.mintlify](https://spacesail.mintlify.app/agent-os/introduction)
- Pydantic AI as the agent framework for typed definitions and toolsets. [ai.pydantic](https://ai.pydantic.dev/toolsets/)

Reasons:

- Type-safe agent definitions with validated inputs and outputs.
- Support for 25+ model providers via a unified interface.
- Native Agent Skills support via `pydantic-ai-skills` with progressive disclosure.
- Dependency injection for passing memory and context into agents cleanly.
- Integration with Pydantic Logfire for OpenTelemetry-based observability, tracing, and cost tracking.
- Structured tool definitions that map cleanly to BroCoDDE's tool layer.
- AgentOS provides a production-grade agentic OS for orchestration, memory, and control plane. [docs.agno](https://docs.agno.com/introduction)

### Frontend: Next.js (TypeScript)

- Next.js for the IDE shell. App Router for view-based navigation matching the sidebar (Dashboard, Queue, Observatory, Context, Series).
- Server-side rendering for initial load, client-side interactivity for the Workshop.
- Tailwind CSS for the dark, information-dense aesthetic.
- Real-time streaming of agent responses via SSE from the FastAPI/AgentOS backend. [community.ibm](https://community.ibm.com/community/user/blogs/anjana-m-r/2025/10/03/server-sent-events-the-perfect-match-for-real-time)

### Database: SQLite (MVP) → PostgreSQL (Production)

- SQLite for local development — zero config, single file, handles all BroCoDDE's data.
- PostgreSQL via Supabase for production with real-time subscriptions and auth.

Schema:

- `codde_tasks` — `id`, `title`, `role`, `intent`, `archetype`, `domain`, `series_id`, `stage`, `extraction_transcript`, `skeleton`, `drafts[]`, `lint_results`, `final_content`, `published_at`, `created_at`
- `memory_entries` — `id`, `type`, `text`, `created_at`, `updated_at`
- `knowledge_domains` — `id`, `name`, `color`, `tags[]`, `post_count`
- `published_posts` — `id`, `task_id`, `content`, `metrics{}`, `post_mortem_findings`
- `series` — `id`, `name`, `description`, `archetype`, `task_ids[]`, `progress`

### Voice: Web Speech API (browser) + Whisper API (server)

- Browser-native for quick mic inputs.
- Whisper for uploads or accuracy. [linkedin](https://www.linkedin.com/pulse/server-sent-events-sse-fastapi-manikandan-parasuraman-q07ff)

### Observability: Pydantic Logfire / OpenTelemetry + AgentOS Control Plane

Every agent call traced with: model used, tier, latency, tokens in/out, estimated cost. Observable in the frontend (model tier indicator on agent responses) and in the observatory for aggregate analysis. AgentOS adds environment-level monitoring and memory inspection. [docs.agentops](https://docs.agentops.ai/v2/integrations/agno)

***

## 13. Project Structure

```text
brocodde/
├── backend/                          # Python (FastAPI + Agno AgentOS + Pydantic AI)
│   ├── pyproject.toml                # uv/pip: agno, pydantic-ai, fastapi, uvicorn,
│   │                                 #   pydantic-ai-skills, openai (whisper),
│   │                                 #   httpx, sqlalchemy, alembic
│   ├── app/
│   │   ├── main.py                   # FastAPI app, AgentOS init, CORS, startup, SSE streaming
│   │   ├── config.py                 # Settings: API keys, model tier config, DB URL
│   │   │
│   │   ├── agents/                   # Agent definitions on top of AgentOS
│   │   │   ├── harness.py            # Orchestrator: routes to correct agent/model,
│   │   │   │                         #   composes context, loads skills per stage
│   │   │   ├── interviewer.py        # Agent(model=tier2, system_prompt=..., tools=[...])
│   │   │   ├── strategist.py         # Agent(model=tier3, ...)
│   │   │   ├── shaper.py             # Agent(model=tier2, ...)
│   │   │   ├── analyst.py            # Agent(model=tier3, ...)
│   │   │   └── tools.py              # tool definitions: memory_read/write,
│   │   │                             #   lint_draft, format_for_platform, etc.
│   │   │
│   │   ├── skills/                   # Agent Skills repository (SKILL.md files)
│   │   │   ├── content-discovery/
│   │   │   │   └── SKILL.md
│   │   │   ├── content-extraction/
│   │   │   │   ├── SKILL.md
│   │   │   │   └── references/
│   │   │   │       ├── role-researcher.md
│   │   │   │       ├── role-illustrator.md
│   │   │   │       └── role-communicator.md
│   │   │   ├── content-vetting/
│   │   │   │   ├── SKILL.md
│   │   │   │   └── references/lint-rules.md
│   │   │   ├── post-mortem-analysis/
│   │   │   │   └── SKILL.md
│   │   │   ├── audience-psychology/
│   │   │   │   ├── SKILL.md
│   │   │   │   └── references/
│   │   │   ├── framework-library/
│   │   │   │   ├── SKILL.md
│   │   │   │   └── references/
│   │   │   ├── platform-linkedin/
│   │   │   │   └── SKILL.md
│   │   │   ├── visual-explanation/
│   │   │   │   └── SKILL.md
│   │   │   ├── communication-bridge/
│   │   │   │   └── SKILL.md
│   │   │   ├── grammar-style/
│   │   │   │   └── SKILL.md
│   │   │   └── series-management/
│   │   │       └── SKILL.md
│   │   │
│   │   ├── memory/                   # Memory and state management
│   │   │   ├── store.py              # CRUD for all memory layers
│   │   │   ├── models.py             # Pydantic models: MemoryEntry, Domain, etc.
│   │   │   ├── knowledge_graph.py    # Domain/tag graph operations
│   │   │   ├── patterns.py           # Performance pattern computation
│   │   │   └── context_composer.py   # Compose context per agent + stage
│   │   │
│   │   ├── models/                   # AI model routing / tier config
│   │   │   ├── router.py             # Tier → model selection, provider dispatch
│   │   │   └── config.py             # tier1/tier2/tier3 model assignments
│   │   │
│   │   ├── tools/                    # External integrations
│   │   │   ├── web_search.py         # Brave/Serper search API
│   │   │   ├── transcription.py      # Whisper API wrapper
│   │   │   └── export.py             # Task export (JSON/Markdown)
│   │   │
│   │   ├── db/                       # Database layer
│   │   │   ├── database.py           # SQLAlchemy engine + session
│   │   │   ├── models.py             # ORM models
│   │   │   └── migrations/           # Alembic migrations
│   │   │
│   │   └── routes/                   # API endpoints
│   │       ├── tasks.py              # POST /tasks, GET /tasks/:id,
│   │       │                         #   PATCH /tasks/:id/stage
│   │       ├── chat.py               # POST /tasks/:id/chat (SSE streaming response)
│   │       ├── memory.py             # CRUD /memory, /domains, /knowledge-graph
│   │       ├── metrics.py            # POST /tasks/:id/metrics, GET /observatory
│   │       ├── series.py             # CRUD /series
│   │       └── skills.py             # GET /skills, GET /skills/:name
│   │
│   └── tests/
│       ├── test_agents.py
│       ├── test_memory.py
│       ├── test_routing.py
│       └── test_skills.py
│
├── frontend/                         # Next.js (TypeScript + Tailwind)
│   ├── package.json
│   ├── next.config.ts
│   ├── tailwind.config.ts            # Dark theme tokens, monospace + sans fonts
│   │
│   ├── app/
│   │   ├── layout.tsx                # Root layout: sidebar + main area
│   │   ├── page.tsx                  # Redirect to /dashboard
│   │   ├── dashboard/page.tsx        # Dashboard (mockup 2)
│   │   ├── queue/page.tsx            # Publish queue (mockup 3)
│   │   ├── observatory/page.tsx      # Content performance (mockup 4)
│   │   ├── context/page.tsx          # Knowledge graph + memory (mockup 5)
│   │   ├── series/page.tsx           # Content series (mockup 6)
│   │   └── task/[id]/page.tsx        # Workshop / CoDDE-task workspace (mockup 7)
│   │
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Sidebar.tsx           # Nav + active task + recent + stats
│   │   │   └── StatusBar.tsx         # Bottom bar: version, task ID, stage, "Pracha Labs"
│   │   ├── task/
│   │   │   ├── LifecycleBar.tsx      # 7-stage progress indicator (mockup 7 top)
│   │   │   ├── RoleSelector.tsx      # Role grid (mockup 1)
│   │   │   ├── IntentSelector.tsx    # Intent selection (step 2)
│   │   │   ├── Chat.tsx              # Chat with streaming + agent indicator
│   │   │   ├── VoiceInput.tsx        # Mic button → Web Speech API → text
│   │   │   ├── DraftEditor.tsx       # Writing area for Drafting stage
│   │   │   ├── LintBadges.tsx        # Pass/warn badges (mockup 2/3)
│   │   │   └── ConfigPanel.tsx       # Right panel: stage, role, intent, metrics,
│   │   │                             #   context loaded (mockup 7 right side)
│   │   ├── dashboard/
│   │   │   ├── StatsCards.tsx         # Total saves, posts, top archetype, top domain
│   │   │   ├── InProgress.tsx         # Active CoDDE-tasks
│   │   │   ├── ReadyToPublish.tsx     # Queue preview with lint badges
│   │   │   └── RecentPerformance.tsx  # Recent post metric cards
│   │   ├── observatory/
│   │   │   ├── AggregateStats.tsx     # Avg impressions, save rate, comments, trend
│   │   │   ├── SaveRateChart.tsx      # Line chart over time
│   │   │   └── PublishedTable.tsx     # Table: task, title, role, metrics
│   │   ├── context/
│   │   │   ├── DomainGrid.tsx         # Domain cards with tags + post counts
│   │   │   ├── MemoryList.tsx         # Identity memory entries with type badges
│   │   │   └── UploadContext.tsx      # File upload for transcripts/docs
│   │   └── series/
│   │       ├── SeriesCard.tsx         # Series with progress bar + metadata
│   │       └── NewSeriesDialog.tsx
│   │
│   ├── lib/
│   │   ├── api.ts                    # Fetch wrapper for backend API
│   │   ├── sse.ts                    # SSE client for streaming chat
│   │   └── types.ts                  # TypeScript types matching backend models
│   │
│   └── styles/
│       └── globals.css               # Tailwind base + custom scrollbar + animations
│
├── docker-compose.yml                # Backend + frontend + optional PostgreSQL
├── .env.example                      # API keys, model config, DB URL
└── README.md
```

***

## 14. Frontend Design (from Mockups)

### Design Language

Dark theme with warm gold (`#D4A853`) as primary accent. Monospaced font (JetBrains Mono) for system elements (task IDs, metrics, labels, status bar). Sans-serif (DM Sans) for content and navigation. Information-dense, professional, IDE-like.

### Layout Architecture

- Persistent left sidebar (220px): BroCoDDE logo + version, navigation (Dashboard, Queue, Observatory, Context, Series), active task card (ID + title + stage), recent tasks list, aggregate stats (Posts, Saves, Queue, Week progress).
- Persistent bottom status bar: version, active task ID, current stage, "Pracha Labs" branding.

### View-by-View Design

- **Dashboard (mockup 2)**: Greeting with weekly progress. Four stat cards (total saves, total posts, top archetype, top domain). In-progress CoDDE-tasks. Ready-to-publish previews with lint badges. Recent performance metric cards side by side.
- **Role Selection (mockup 1)**: Breadcrumb flow ROLE → INTENT → BEGIN. Grid of role cards (2 columns, 6 rows) with icon, name, one-line description, and arrow. Clean, focused selection.
- **Workshop (mockup 7)**: Three-column layout. Top bar: task ID, role icon + name, intent. Lifecycle bar with all 7 stages as pills (active stage highlighted gold). Center: chat area with agent responses streaming. Bottom: text input with send button + voice mic button. Right panel: current stage description, configuration (role, intent, metric target), and context loaded indicators.
- **Queue (mockup 3)**: Title "1 ready to publish." Each draft card shows: task ID, title, metadata row (role icon + intent + series link), draft content preview in monospaced text, lint badges (pass in green, warning in amber).
- **Observatory (mockup 4)**: Four aggregate cards (avg impressions, avg save rate, avg comments, trend percentage). Save rate chart over time (line chart, months on x-axis). Published content table with columns: task ID, title, role icon, impressions, saves, save rate (highlighted in gold/green), comments, DMs.
- **Context (mockup 5)**: "Knowledge Graph" heading with Upload Context and Add Entry buttons. Domain grid: colored dot + name + tag pills + post count per card. Identity Memory list: type badge (Experience, Research, Collaboration, Philosophy, Current) + description + edit icon per row.
- **Series (mockup 6)**: "3 Active Series" heading with New Series button. Each series card: icon + title + description + progress (3/5 posts) + archetype badge + last date + progress bar.

***

## 15. Observability

### Content-Level

Full traceability per CoDDE-task: every decision, extraction exchange, draft version, lint result, post-mortem finding.

### Pattern-Level

Across tasks: save rates by archetype (see Observatory), engagement by domain, audience ring penetration, role effectiveness, optimal timing.

### System-Level

Practice health: posting cadence, lifecycle completion rate, average time per stage, improvement trends, model usage and cost per task, memory growth rate. [contentful](https://www.contentful.com/blog/content-lifecycle/)

### Model-Level

Every API call logged: model, tier, latency, tokens in/out, estimated cost. Visible as a tier indicator on agent responses and aggregated in Observatory. AgentOS and Pydantic Logfire/OpenTelemetry provide additional tracing and metrics. [docs.agentops](https://docs.agentops.ai/v2/integrations/agno)

***

## 16. User Flows

### Flow 1: New CoDDE-Task (The Daily Build)

Click "+ New CoDDE-Task" → Role selection grid (mockup 1) → Choose role → Intent selection → BEGIN → Workshop opens (mockup 7) with lifecycle bar at Discovery → Strategist agent loads context and provides Discovery brief → User picks direction → Stage advances to Extraction → Interviewer agent conducts interview → After sufficient material, Shaper suggests archetype → Structuring stage: skeleton built → Drafting stage: user writes in editor → Vetting stage: lint checks, feedback → When cleared, moves to Ready → Appears in Queue (mockup 3).

### Flow 2: Publishing and Post-Mortem

User publishes externally on LinkedIn → Returns to BroCoDDE → Opens published task → Reports metrics via chat → Analyst agent (Tier 3) conducts post-mortem → Findings stored → Task closed → Data feeds into Observatory (mockup 4) and future Discovery briefs.

### Flow 3: Context Update

Open Context view (mockup 5) → Click "+ Add Entry" → Add new memory entry with type badge → Or click "Upload Context" → Upload transcript/document → Or click edit icon on existing entry → Modify inline → Changes immediately available to all future agent calls.

***

## 17. What BroCoDDE Is

A Content Development Life Cycle engine. An IDE where deep expertise becomes meticulously designed professional content through a structured, agent-assisted process. A holistic platform: Python backend with Agno AgentOS and Pydantic AI agents equipped with progressive-disclosure skills, a Next.js frontend designed as a professional IDE, tiered AI model routing, six-layer memory architecture, and three-level observability. [github](https://github.com/agno-agi/agno)

The human builds. The IDE enables. Every CoDDE-task makes both smarter.

***

## 18. What BroCoDDE Is Not

Not an autonomous content agent. Not a content generator. Not a social media scheduler. Not a growth-hack system. Not locked to a single AI provider. Not about vanity metrics. It's about building intellectual credibility with the right people through engineered content.

***

Project BroCoDDE — Because the best content isn't created. It's engineered.