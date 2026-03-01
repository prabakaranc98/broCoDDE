# SKILL: Agno Architecture for BroCoDDE
## Definitive Design Reference — v2

This skill documents every Agno design decision made for BroCoDDE, the rationale,
and what NOT to do. Written from direct doc analysis + implementation experience.

---

## 1. What BroCoDDE Is (Agno framing)

BroCoDDE is a **single-user, multi-session, multi-agent content lifecycle system**.

| Dimension | Value |
|---|---|
| Users | 1 (single creator) |
| Tasks (sessions) | Many (one per piece of content) |
| Agents | 4 specialists, one active per lifecycle stage |
| Lifecycle | 7 stages — deterministic sequence |
| State | Per-task (session_id = task_id) + per-user (memory_manager) |

---

## 2. Primitive Selection — What to Use and Why

### Individual Agents (NOT Workflow, NOT Team — for now)

**Decision:** Use 4 separate Agno `Agent` instances routed by the harness.

**Why not Workflow?**
- BroCoDDE is interactive — the user drives each stage's pacing, not a pipeline
- `Workflow.steps` execute sequentially and auto-advance — wrong for conversational lifecycle
- Users may have 20 turns in Extraction before moving to Structuring
- Workflow is right when steps have defined I/O; here output of each stage is open-ended conversation

**Why not Team (yet)?**
- Team is right when multiple agents need to collaborate *simultaneously* on a single task
- Currently each lifecycle stage is handled by one agent — no real-time collaboration needed
- Future use: `Team(mode=coordinate, members=[shaper, analyst])` for deep vetting critique

**Current routing (harness.py):**
```python
STAGE_AGENT_MAP = {
    "discovery":   "strategist",   # Tier 3
    "extraction":  "interviewer",  # Tier 2
    "structuring": "shaper",       # Tier 2
    "drafting":    "shaper",       # Tier 2
    "vetting":     "shaper",       # Tier 2-3
    "ready":       "shaper",       # Tier 2
    "post-mortem": "analyst",      # Tier 3
}
```

**Future Team pattern for vetting:**
```python
vetting_team = Team(
    mode=TeamMode.coordinate,
    members=[build_shaper("vetting"), build_analyst()],
    add_team_history_to_members=True,
    session_id=task_id,
)
```

---

## 3. Session Management

### session_id = task_id (STABLE)

```python
# harness.py
session_id = session_id or task_id   # NOT f"{task_id}-{stage}"
```

**Why stable session_id matters:**
When session_id changes per stage, Agno starts a new session → `add_history_to_context` gets nothing.
With `session_id = task_id`, all stages share one Agno session → full conversation history flows through.

**What Agno stores per session:**
```
agno_sessions:
  session_id  = task_id (stable across all 7 stages)
  agent_id    = changes per stage (strategist, interviewer, ...)
  runs        = [{user_msg, agent_response, tools_called, ...}]
```

### user_id = "default_user" (single-user)
Since BroCoDDE is single-user, `user_id` is fixed. Cross-task patterns accumulate
under one user in `agno_memories`. No multi-tenant isolation needed.

---

## 4. Chat History (Conversational Continuity)

### Enabled on all 4 agents:
```python
Agent(
    add_history_to_context=True,   # inject prior turns into each new request
    num_history_runs=10,           # look back 10 runs within the same session
    db=agno_db,                    # required — without DB, no history persists
    session_id=task_id,            # stable session ensures history accumulates
)
```

### Two parallel history stores:
1. **Agno session history** (`agno_sessions`) — used for `add_history_to_context` in reasoning
2. **App `chat_history`** (`codde_tasks.chat_history`) — used by frontend to render messages

They are independent. App's `chat_history` = display layer. Agno's session = reasoning layer.

---

## 5. Two-Layer Context Architecture

### Core distinction:
```
source="user"  → What the human explicitly told the system
source="agent" → What agents extracted/inferred from conversations
```

### User Context (human-curated)
Types: `Experience | Research | Collaboration | Philosophy | Current | Voice | Goal`

Set via `/memory` API. Injected into ALL agent prompts. Humans write these; agents never modify them.

### Agent Context (machine-derived)
Types: `Pattern | Insight | Hypothesis | Finding | Structural`

Written by agents via `memory_write_tool()` (always `source="agent"`).
Filtered by `lifecycle_phases` — agents only see what's relevant to their stage.

### lifecycle_phases filtering:
```python
# [] = inject at all stages (global context)
# ["discovery"] = only inject during Discovery
# ["discovery", "post-mortem"] = inject in those two phases

# Analyst writes a post-mortem finding for future Discovery:
await memory_write_tool(
    memory_type="Finding",
    text="Framework Drop posts get 2x save rate vs Field Notes in AI domain.",
    tags=["Framework Drop", "AI", "save_rate"],
    lifecycle_phases=["discovery"],  # only surfaces when Strategist opens next task
)
```

### compose_context() output (rendered in system prompt):
```
## User Context (human-provided)
- [Voice] I write in first person, short paragraphs
- [Experience] 8 years in ML infrastructure
- [Goal] Reach 10k LinkedIn followers by Q4

## Derived Context (agent-learned)
- [Pattern] (Framework Drop, AI) Framework Drop: avg 4.7% save rate (n=12)
- [Finding] (AI, Tuesday) AI infra content peaks on Tuesday mornings
- [Hypothesis] Specificity in the hook increases saves by ~40%

## Knowledge Domains
- Machine Learning [ML, LLMs, infra] (8 posts)

## Performance Patterns
- Framework Drop: 4.7% (12 posts)
- Field Note: 2.1% (5 posts)
```

### Agno MemoryManager (third layer — semantic extraction):
```python
MemoryManager(
    db=agno_db,
    model=tier1_model,
    additional_instructions="Extract user expertise, voice patterns, domain ownership..."
)
```
With `update_memory_on_run=True`: tier1 reads every conversation and extracts durable facts
to `agno_memories`. Separate from app's `MemoryEntry` — Agno manages its own table.

---

## 6. Discovery Tools — ContentDiscoveryToolkit

All discovery signals are unified in one Agno `Toolkit`:
**`app/agents/content_discovery_toolkit.py` → `ContentDiscoveryToolkit`**

```python
# Strategist agent tools list
tools=[
    memory_tools,
    ContentDiscoveryToolkit(),   # ALL six discovery tools in one bundle
    web_fetch_tool,              # direct URL reader for deeper reads
    skill_list, skill_load,
    compute_patterns_tool,
]
```

### Six tools — what each answers:

| Tool               | Source          | Question answered                                  |
|--------------------|-----------------|---------------------------------------------------|
| get_hf_daily_papers | HuggingFace Hub | What's trending in AI research TODAY?             |
| search_hf_papers   | HuggingFace Hub | What papers exist on topic X? (by upvotes)         |
| search_hackernews  | HN Algolia API  | What are devs/founders actually debating?          |
| search_news        | Exa (news)      | What is mainstream tech media covering?            |
| search_research    | Exa (research)  | What academic research exists beyond HF?           |
| search_underrated  | Exa (niche)     | What angles are in substacks/blogs, not mainstream?|

### Signal pairing strategy:
```
HF papers + HN discourse = the research-practitioner GAP
→ "Bridge" content: translate what research knows that practitioners don't yet

search_news vs search_underrated = the mainstream-niche GAP
→ "Underrated angle" content: own the topic before it goes mainstream

search_hf_papers + search_research = full academic depth on a specific topic
→ Use when user wants to write something research-grounded
```

### Implementation notes:
- **Package:** `huggingface-hub>=1.0.0` — `list_daily_papers` added in v1.0
- **No auth token needed** — HF daily papers are public
- **Toolkit pattern:** extends `agno.tools.Toolkit`, all methods are sync (Agno handles thread dispatch)
- **Exa fallback:** gracefully returns hint message if `EXA_API_KEY` not set
- **HN via Algolia:** uses `https://hn.algolia.com/api/v1/search` — no API key required
- `search_underrated` targets niche domains (substack, lesswrong, personal ML blogs) first,
  falls back to broader Exa search with "underrated overlooked niche" modifier

---

## 7. Guardrails — Right-Sized for BroCoDDE

### What to guard (single-user content tool):

**Content quality guardrail = lint_draft_tool**
The lint tool catches: rant, fluff, engagement_bait, credential_stating, opening weakness, micro_learning.
This IS the output guardrail. It's purpose-built for the domain.

**Tone guardrail = UNIVERSAL_SYSTEM_PROMPT**
Governs: no robotic AI-speak, no exclamation spam, match user velocity.
Applied to ALL agents via base.py injection.

**What NOT to add:**
- PII detection (single user, no PII risk)
- Toxicity filtering (creator controls their content)
- Hard topic refusals (creator owns their angles)
- Rate limiting beyond what OpenRouter provides (single user)

**If Agno guardrails are ever needed (future):**
```python
from agno.guardrails import Guardrails, InputGuard, OutputGuard
Agent(
    guardrails=Guardrails(
        input=[InputGuard(max_chars=10000)],
        output=[OutputGuard(max_chars=8000)],
    )
)
```

---

## 8. Human-in-the-Loop

### Current HITL: [ADVANCE_STAGE] macro
The agent includes `[ADVANCE_STAGE]` at the end of its response ONLY when the user explicitly
greenlights moving forward. Frontend detects this and auto-advances the lifecycle stage.

**This is intentional, lightweight HITL** — the human controls pacing; agents never force-advance.

### Why no formal Agno HITL hooks:
- Agents cannot publish content (always human-reviewed before publishing)
- Agents cannot delete user data
- Agents cannot send external messages
- The only "risky" agent action is `memory_write_tool` — acceptable without approval for now

**Future consideration:** If Analyst's findings need human approval before persisting,
add HITL before `memory_write_tool` calls in post-mortem.

---

## 9. Reasoning Agents

### Current: Standard agents (reasoning=False)

**When to enable reasoning:**
```python
# Analyst — causal post-mortem analysis
Agent(reasoning=True, reasoning_min_steps=2, reasoning_max_steps=8, ...)

# Strategist — evaluating 3 content angles requires structured comparison
Agent(reasoning=True, reasoning_min_steps=1, reasoning_max_steps=5, ...)
```

**Cost:** Reasoning adds 2-8 extra LLM calls per run. At Tier 3, expensive.
Enable only for Analyst (post-mortem) and Strategist (discovery brief generation).
NOT for Interviewer (conversational, fast) or Shaper (reactive, iterative).

**Not implemented yet.** Add when Analyst's causal hypotheses need more rigor.

---

## 10. Context Engineering

### System message composition order (cache-optimal):
1. UNIVERSAL_SYSTEM_PROMPT — static, at top → best caching hit rate
2. Role-specific instructions — semi-static
3. Composed context (user + agent context, domains, patterns) — dynamic, injected by compose_context()
4. Chat history — injected by `add_history_to_context`
5. User message

**Caching:** Anthropic/OpenAI cache prefixes. UNIVERSAL_SYSTEM_PROMPT at the very top
of every agent's instructions maximizes cache hits across all 4 agents.

### What NOT to put in the system prompt:
- Real-time web search results (put in tool response text)
- Full chat_history manually (use `add_history_to_context=True` instead)
- Task-specific drafts (user pastes these in the user message)

---

## 11. Feature Decision Table

| Agno Feature | Used | Reason |
|---|---|---|
| `Agent` | YES | Core primitive |
| `MemoryManager` | YES | Cross-session user fact extraction |
| `add_history_to_context` | YES | Multi-turn conversational continuity |
| `num_history_runs=10` | YES | Look back 10 turns within session |
| Stable `session_id=task_id` | YES | All stages share one Agno session |
| `ContentDiscoveryToolkit` | YES | Unified: HF papers + HN + Exa (news/research/underrated) |
| `HackerNewsTools` (standalone) | NO | Replaced — HN now inside ContentDiscoveryToolkit |
| `web_search_tool` (standalone) | NO (on Strategist) | Replaced — Exa now inside ContentDiscoveryToolkit; still used by Analyst |
| Two-layer context (user/agent) | YES | Provenance-aware context injection |
| `lifecycle_phases` filtering | YES | Agents only see phase-relevant context |
| `Workflow` | NO | Interactive chat, not sequential pipeline |
| `Team` | NOT YET | Add for vetting collaboration |
| `reasoning=True` | NOT YET | Add for Analyst + Strategist |
| Agno formal guardrails | NOT YET | lint_tool + UNIVERSAL_PROMPT sufficient |
| Agno HITL hooks | NOT YET | [ADVANCE_STAGE] macro is sufficient |
| `output_schema` (Pydantic) | NOT YET | Add for structured stage handoffs |
| `learning=True` | NOT NEEDED | MemoryManager covers the use case |
| Multi-tenant | NOT APPLICABLE | Single user |
| Broadcast/Tasks TeamMode | NOT APPLICABLE | Not collaborative |
