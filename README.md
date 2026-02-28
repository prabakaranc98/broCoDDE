# BroCoDDE

**An IDE for Content Discovery, Development & Enablement**  
*Version 0.4 — Prabakaran Chandran / Pracha Labs*

> The human builds. The IDE enables. Every CoDDE-task makes both smarter.

---

## What It Is

BroCoDDE is a **Content Development Life Cycle (CoDLC) engine**. Every piece of content has a lifecycle, an identity, a lineage, and a feedback loop. The fundamental unit of work is the **CoDDE-task** — a uniquely identified content development cycle that carries its own context, memory, interactions, drafts, metadata, and post-mortem analysis.

Seven lifecycle stages: **Discovery → Extraction → Structuring → Drafting → Vetting → Ready → Post-Mortem**

Four specialized AI agents, tiered model routing, progressive-disclosure skills, and six-layer memory architecture.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12 · FastAPI · Agno AgentOS · Pydantic AI |
| Frontend | Next.js 15 · TypeScript · Tailwind CSS |
| Database | SQLite (dev) → PostgreSQL (production) |
| AI | Anthropic Claude · OpenAI GPT · Ollama (local) |
| Observability | Pydantic Logfire · AgentOS Control Plane |

---

## Quickstart

### 1. Clone and configure

```bash
git clone https://github.com/prabakaranc98/broCoDDE
cd broCoDDE
cp .env.example .env
# Edit .env and add at minimum ANTHROPIC_API_KEY or OPENAI_API_KEY
```

### 2. Backend

```bash
cd backend
# Install dependencies (uv recommended)
pip install uv
uv pip install -e ".[dev]"

# Run migrations
alembic upgrade head

# Start backend (with demo seed data)
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
# Open http://localhost:3000
```

### 4. Docker (optional)

```bash
docker compose up backend frontend
```

---

## Project Structure

```
brocodde/
├── backend/          # Python · FastAPI · Agno AgentOS · Pydantic AI
│   ├── app/
│   │   ├── agents/   # Interviewer · Strategist · Shaper · Analyst
│   │   ├── skills/   # 13 SKILL.md files (progressive disclosure)
│   │   ├── memory/   # 6-layer memory architecture
│   │   ├── models/   # Tiered model routing
│   │   ├── tools/    # web_search · transcription · export
│   │   ├── routes/   # FastAPI endpoints
│   │   └── db/       # SQLAlchemy + Alembic
│   └── tests/
└── frontend/         # Next.js · TypeScript · Tailwind
    ├── app/          # Dashboard · Queue · Observatory · Context · Series · Workshop
    ├── components/   # Layout · Task · Dashboard · Observatory · Context · Series
    └── lib/          # API client · SSE streaming · TypeScript types
```

---

## Views

| View | Route | Description |
|---|---|---|
| Dashboard | `/dashboard` | Weekly progress, active tasks, queue preview |
| Workshop | `/task/[id]` | Main CoDDE-task workspace with lifecycle bar |
| Queue | `/queue` | Ready-to-publish drafts with lint badges |
| Observatory | `/observatory` | Aggregate performance analytics |
| Context | `/context` | Knowledge graph + identity memory |
| Series | `/series` | Content series management |

---

## Design Language

Dark IDE aesthetic. Warm gold (`#D4A853`) accent. **JetBrains Mono** for system elements + **DM Sans** for content. Information-dense, professional.

---

*Project BroCoDDE — Because the best content isn't created. It's engineered.*
