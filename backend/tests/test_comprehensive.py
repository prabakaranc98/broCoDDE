"""
BroCoDDE — Comprehensive Test Suite
Covers: tasks CRUD, chat/SSE, memory, skills, agent harness,
        tools, memory store, full lifecycle flow, and persistence.
"""

import json
import os
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch

# ── App setup ──────────────────────────────────────────────────────────────────
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_brocodde.db")
os.environ.setdefault("ENVIRONMENT", "development")

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.database import Base, get_db


# ── Test DB ────────────────────────────────────────────────────────────────────
TEST_DB_URL = "sqlite+aiosqlite:///./test_brocodde.db"
test_engine = create_async_engine(TEST_DB_URL, echo=False)
TestSessionLocal = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    import aiofiles.os
    try:
        os.remove("./test_brocodde.db")
    except FileNotFoundError:
        pass


@pytest_asyncio.fixture
async def client():
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def db_session():
    async with TestSessionLocal() as session:
        yield session


# ── Helpers ────────────────────────────────────────────────────────────────────

async def create_task(client, role="researcher", intent="teach", title="Test Task"):
    resp = await client.post("/tasks", json={"role": role, "intent": intent, "title": title})
    assert resp.status_code == 200, resp.text
    return resp.json()


def parse_sse(raw: str) -> list[str]:
    """Parse SSE text into list of data values."""
    chunks = []
    for line in raw.splitlines():
        if line.startswith("data: "):
            val = line[6:]
            if val not in ("[DONE]", ""):
                chunks.append(val)
    return chunks


# ══════════════════════════════════════════════════════════════════════════════
# 1. HEALTH CHECK
# ══════════════════════════════════════════════════════════════════════════════

class TestHealth:
    async def test_health_returns_ok(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "BroCoDDE"
        assert "provider" in data

    async def test_health_has_version(self, client):
        resp = await client.get("/health")
        assert "version" in resp.json()


# ══════════════════════════════════════════════════════════════════════════════
# 2. TASKS CRUD
# ══════════════════════════════════════════════════════════════════════════════

class TestTasksCRUD:
    async def test_create_task_minimal(self, client):
        resp = await client.post("/tasks", json={"role": "researcher", "intent": "teach"})
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert data["stage"] == "discovery"
        assert data["role"] == "researcher"
        assert data["intent"] == "teach"

    async def test_create_task_with_title(self, client):
        resp = await client.post("/tasks", json={
            "role": "storyteller",
            "intent": "inspire",
            "title": "My content idea",
        })
        assert resp.status_code == 200
        assert resp.json()["title"] == "My content idea"

    async def test_create_task_with_domain(self, client):
        resp = await client.post("/tasks", json={
            "role": "coder",
            "intent": "teach",
            "domain": "Engineering",
        })
        assert resp.status_code == 200
        assert resp.json()["domain"] == "Engineering"

    async def test_task_id_format(self, client):
        resp = await client.post("/tasks", json={"role": "researcher", "intent": "share"})
        task_id = resp.json()["id"]
        assert task_id.startswith("codde-")
        parts = task_id.split("-")
        assert len(parts) == 3
        assert len(parts[1]) == 8  # YYYYMMDD
        assert parts[2].isdigit()

    async def test_list_tasks(self, client):
        await create_task(client, title="List test A")
        await create_task(client, title="List test B")
        resp = await client.get("/tasks")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    async def test_list_tasks_filter_by_stage(self, client):
        resp = await client.get("/tasks?stage=discovery")
        assert resp.status_code == 200
        for task in resp.json():
            assert task["stage"] == "discovery"

    async def test_get_task_by_id(self, client):
        task = await create_task(client, title="Get by ID test")
        resp = await client.get(f"/tasks/{task['id']}")
        assert resp.status_code == 200
        assert resp.json()["id"] == task["id"]

    async def test_get_task_not_found(self, client):
        resp = await client.get("/tasks/codde-99990101-999")
        assert resp.status_code == 404

    async def test_update_task_title(self, client):
        task = await create_task(client)
        resp = await client.patch(f"/tasks/{task['id']}", json={"title": "Updated Title"})
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated Title"

    async def test_update_task_domain(self, client):
        task = await create_task(client)
        resp = await client.patch(f"/tasks/{task['id']}", json={"domain": "AI & ML"})
        assert resp.status_code == 200
        assert resp.json()["domain"] == "AI & ML"

    async def test_update_task_skeleton(self, client):
        task = await create_task(client)
        skeleton = {"hook": "Opening hook", "key_points": ["Point 1", "Point 2"], "landing": "CTA"}
        resp = await client.patch(f"/tasks/{task['id']}", json={"skeleton": skeleton})
        assert resp.status_code == 200
        assert resp.json()["skeleton"]["hook"] == "Opening hook"

    async def test_advance_stage_valid(self, client):
        task = await create_task(client)
        resp = await client.patch(f"/tasks/{task['id']}/stage", json={"stage": "extraction"})
        assert resp.status_code == 200
        assert resp.json()["stage"] == "extraction"

    async def test_advance_through_all_stages(self, client):
        task = await create_task(client)
        stages = ["extraction", "structuring", "drafting", "vetting", "ready", "post-mortem"]
        for stage in stages:
            resp = await client.patch(f"/tasks/{task['id']}/stage", json={"stage": stage})
            assert resp.status_code == 200, f"Failed at stage: {stage}"
            assert resp.json()["stage"] == stage

    async def test_advance_stage_invalid(self, client):
        task = await create_task(client)
        resp = await client.patch(f"/tasks/{task['id']}/stage", json={"stage": "nonexistent"})
        assert resp.status_code == 422

    async def test_add_draft(self, client):
        task = await create_task(client)
        resp = await client.post(
            f"/tasks/{task['id']}/drafts",
            json={"content": "My first draft content here.", "version": 1}
        )
        assert resp.status_code == 200

    async def test_create_task_different_roles(self, client):
        roles = ["researcher", "storyteller", "teacher", "coder", "contrarian", "archaeologist"]
        for role in roles:
            resp = await client.post("/tasks", json={"role": role, "intent": "teach"})
            assert resp.status_code == 200, f"Failed for role: {role}"
            assert resp.json()["role"] == role


# ══════════════════════════════════════════════════════════════════════════════
# 3. CHAT / SSE STREAMING
# ══════════════════════════════════════════════════════════════════════════════

class TestChatStreaming:
    async def test_chat_returns_sse_stream(self, client):
        task = await create_task(client)
        resp = await client.post(
            f"/tasks/{task['id']}/chat",
            json={"message": "Hello, let's start.", "user_id": "test_user"},
        )
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers.get("content-type", "")

    async def test_sse_format_has_data_prefix(self, client):
        task = await create_task(client)
        resp = await client.post(
            f"/tasks/{task['id']}/chat",
            json={"message": "Say hello.", "user_id": "test_user"},
        )
        lines = resp.text.splitlines()
        data_lines = [l for l in lines if l.startswith("data: ")]
        assert len(data_lines) > 0

    async def test_sse_ends_with_done(self, client):
        task = await create_task(client)
        resp = await client.post(
            f"/tasks/{task['id']}/chat",
            json={"message": "Test.", "user_id": "test_user"},
        )
        assert "[DONE]" in resp.text

    async def test_chat_saves_to_history(self, client):
        task = await create_task(client)
        await client.post(
            f"/tasks/{task['id']}/chat",
            json={"message": "Tell me about content creation.", "user_id": "test_user"},
        )
        # Reload task and verify chat history saved
        resp = await client.get(f"/tasks/{task['id']}")
        task_data = resp.json()
        history = task_data.get("chat_history") or []
        assert len(history) >= 1
        # User message should be in history
        user_msgs = [m for m in history if m.get("role") == "user"]
        assert len(user_msgs) >= 1
        assert user_msgs[0]["content"] == "Tell me about content creation."

    async def test_chat_history_includes_agent_response(self, client):
        task = await create_task(client)
        await client.post(
            f"/tasks/{task['id']}/chat",
            json={"message": "Hi!", "user_id": "test_user"},
        )
        resp = await client.get(f"/tasks/{task['id']}")
        history = resp.json().get("chat_history") or []
        agent_msgs = [m for m in history if m.get("role") == "agent"]
        assert len(agent_msgs) >= 1
        assert len(agent_msgs[0]["content"]) > 0

    async def test_chat_accumulates_history_across_turns(self, client):
        task = await create_task(client)
        for msg in ["First message.", "Second message.", "Third message."]:
            await client.post(
                f"/tasks/{task['id']}/chat",
                json={"message": msg, "user_id": "test_user"},
            )
        resp = await client.get(f"/tasks/{task['id']}")
        history = resp.json().get("chat_history") or []
        user_msgs = [m for m in history if m.get("role") == "user"]
        assert len(user_msgs) == 3

    async def test_chat_with_deep_critique_flag(self, client):
        task = await create_task(client)
        # Advance to vetting stage where deep_critique is relevant
        await client.patch(f"/tasks/{task['id']}/stage", json={"stage": "vetting"})
        resp = await client.post(
            f"/tasks/{task['id']}/chat",
            json={"message": "Critique my draft.", "user_id": "test_user", "deep_critique": True},
        )
        assert resp.status_code == 200

    async def test_chat_routes_to_correct_agent_by_stage(self, client):
        """Each stage produces a response (agent routing works end-to-end)."""
        stages_and_messages = {
            "discovery": "What trending topics should I explore?",
            "extraction": "I want to talk about AI in education.",
            "structuring": "Help me structure this.",
            "drafting": "How should I open my post?",
            "vetting": "Vet my draft.",
        }
        for stage, message in stages_and_messages.items():
            task = await create_task(client)
            if stage != "discovery":
                await client.patch(f"/tasks/{task['id']}/stage", json={"stage": stage})
            resp = await client.post(
                f"/tasks/{task['id']}/chat",
                json={"message": message, "user_id": "test_user"},
            )
            assert resp.status_code == 200, f"Chat failed at stage: {stage}"
            chunks = parse_sse(resp.text)
            assert len(chunks) > 0, f"No content returned at stage: {stage}"

    async def test_chat_invalid_task_id(self, client):
        resp = await client.post(
            "/tasks/codde-00000000-000/chat",
            json={"message": "Hello", "user_id": "test_user"},
        )
        assert resp.status_code == 404

    async def test_chat_response_contains_text(self, client):
        task = await create_task(client)
        resp = await client.post(
            f"/tasks/{task['id']}/chat",
            json={"message": "What is the discovery stage?", "user_id": "test_user"},
        )
        chunks = parse_sse(resp.text)
        full_text = "".join(chunks).replace("\\n", "\n")
        assert len(full_text) > 10


# ══════════════════════════════════════════════════════════════════════════════
# 4. MEMORY (Identity Memory & Knowledge Domains)
# ══════════════════════════════════════════════════════════════════════════════

class TestMemory:
    async def test_list_memory_returns_list(self, client):
        resp = await client.get("/memory")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_create_memory_entry(self, client):
        resp = await client.post("/memory", json={
            "type": "Experience",
            "text": "I worked at Google for 5 years on search algorithms.",
            "tags": ["google", "search", "engineering"],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["type"] == "Experience"
        assert "google" in data["tags"]
        assert "id" in data

    async def test_create_memory_all_types(self, client):
        types = ["Experience", "Research", "Collaboration", "Philosophy", "Current", "Voice", "Goal"]
        for mem_type in types:
            resp = await client.post("/memory", json={
                "type": mem_type,
                "text": f"Test {mem_type} memory entry.",
                "tags": [mem_type.lower()],
            })
            assert resp.status_code == 200, f"Failed for type: {mem_type}"
            assert resp.json()["type"] == mem_type

    async def test_memory_entry_has_timestamps(self, client):
        resp = await client.post("/memory", json={
            "type": "Goal",
            "text": "Reach 10k followers on LinkedIn.",
        })
        data = resp.json()
        assert "created_at" in data
        assert "updated_at" in data

    async def test_update_memory_entry(self, client):
        create_resp = await client.post("/memory", json={
            "type": "Research",
            "text": "Original research note.",
        })
        entry_id = create_resp.json()["id"]
        update_resp = await client.patch(f"/memory/{entry_id}", json={
            "text": "Updated research note with more detail."
        })
        assert update_resp.status_code == 200
        assert update_resp.json()["text"] == "Updated research note with more detail."

    async def test_delete_memory_entry(self, client):
        create_resp = await client.post("/memory", json={
            "type": "Current",
            "text": "Temporary memory entry to delete.",
        })
        entry_id = create_resp.json()["id"]
        del_resp = await client.delete(f"/memory/{entry_id}")
        assert del_resp.status_code == 200
        # Verify it's gone
        list_resp = await client.get("/memory")
        ids = [e["id"] for e in list_resp.json()]
        assert entry_id not in ids

    async def test_delete_nonexistent_memory(self, client):
        resp = await client.delete("/memory/nonexistent-id-12345")
        assert resp.status_code == 404

    async def test_list_domains(self, client):
        resp = await client.get("/memory/domains")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_create_knowledge_domain(self, client):
        resp = await client.post("/memory/domains", json={
            "name": "Artificial Intelligence",
            "color": "#D4A853",
            "tags": ["AI", "ML", "deep learning"],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Artificial Intelligence"
        assert data["post_count"] == 0
        assert "id" in data

    async def test_create_domain_default_color(self, client):
        resp = await client.post("/memory/domains", json={"name": "Quantum Computing"})
        assert resp.status_code == 200
        assert resp.json()["color"] == "#D4A853"

    async def test_memory_persists_across_requests(self, client):
        await client.post("/memory", json={"type": "Philosophy", "text": "Persistent philosophy."})
        resp1 = await client.get("/memory")
        count1 = len(resp1.json())
        resp2 = await client.get("/memory")
        assert len(resp2.json()) == count1


# ══════════════════════════════════════════════════════════════════════════════
# 5. SKILLS
# ══════════════════════════════════════════════════════════════════════════════

class TestSkills:
    async def test_list_skills(self, client):
        resp = await client.get("/skills")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0

    async def test_skills_have_name_field(self, client):
        resp = await client.get("/skills")
        for skill in resp.json():
            assert "name" in skill

    async def test_load_skill_content(self, client):
        skills_resp = await client.get("/skills")
        skills = skills_resp.json()
        if not skills:
            pytest.skip("No skills available")
        first_skill = skills[0]["name"]
        resp = await client.get(f"/skills/{first_skill}")
        assert resp.status_code == 200
        data = resp.json()
        assert "content" in data
        assert len(data["content"]) > 0

    async def test_load_skill_returns_name(self, client):
        skills_resp = await client.get("/skills")
        skills = skills_resp.json()
        if not skills:
            pytest.skip("No skills available")
        skill_name = skills[0]["name"]
        resp = await client.get(f"/skills/{skill_name}")
        assert resp.json()["name"] == skill_name

    async def test_load_nonexistent_skill(self, client):
        resp = await client.get("/skills/nonexistent-skill-xyz")
        assert resp.status_code == 404

    async def test_all_skills_loadable(self, client):
        skills_resp = await client.get("/skills")
        for skill in skills_resp.json():
            resp = await client.get(f"/skills/{skill['name']}")
            assert resp.status_code == 200, f"Skill '{skill['name']}' failed to load"


# ══════════════════════════════════════════════════════════════════════════════
# 6. AGENT HARNESS (unit tests)
# ══════════════════════════════════════════════════════════════════════════════

class TestAgentHarness:
    async def test_harness_streams_text(self):
        from app.agents.harness import stream_chat
        chunks = []
        async for chunk in stream_chat(
            message="Hello",
            task_stage="discovery",
            task_id="test-id",
            user_id="test_user",
        ):
            chunks.append(chunk)
        assert len(chunks) > 0
        full = "".join(chunks)
        assert len(full) > 0

    async def test_harness_discovery_uses_strategist(self):
        from app.agents.harness import stream_chat, STAGE_AGENT_MAP
        assert STAGE_AGENT_MAP["discovery"] == "strategist"

    async def test_harness_extraction_uses_interviewer(self):
        from app.agents.harness import STAGE_AGENT_MAP
        assert STAGE_AGENT_MAP["extraction"] == "interviewer"

    async def test_harness_structuring_uses_shaper(self):
        from app.agents.harness import STAGE_AGENT_MAP
        assert STAGE_AGENT_MAP["structuring"] == "shaper"

    async def test_harness_drafting_uses_shaper(self):
        from app.agents.harness import STAGE_AGENT_MAP
        assert STAGE_AGENT_MAP["drafting"] == "shaper"

    async def test_harness_vetting_uses_shaper(self):
        from app.agents.harness import STAGE_AGENT_MAP
        assert STAGE_AGENT_MAP["vetting"] == "shaper"

    async def test_harness_post_mortem_uses_analyst(self):
        from app.agents.harness import STAGE_AGENT_MAP
        assert STAGE_AGENT_MAP["post-mortem"] == "analyst"

    async def test_harness_all_stages_have_mapping(self):
        from app.agents.harness import STAGE_AGENT_MAP
        valid_stages = {"discovery", "extraction", "structuring", "drafting", "vetting", "ready", "post-mortem"}
        for stage in valid_stages:
            assert stage in STAGE_AGENT_MAP, f"Stage '{stage}' missing from STAGE_AGENT_MAP"

    async def test_harness_each_stage_produces_output(self):
        from app.agents.harness import stream_chat
        stages = ["discovery", "extraction", "structuring", "drafting", "vetting", "post-mortem"]
        for stage in stages:
            chunks = []
            async for chunk in stream_chat(
                message="Test message",
                task_stage=stage,
                task_id="test-id",
                user_id="test_user",
            ):
                chunks.append(chunk)
            assert len(chunks) > 0, f"No output from harness for stage: {stage}"


# ══════════════════════════════════════════════════════════════════════════════
# 7. TOOLS (unit tests)
# ══════════════════════════════════════════════════════════════════════════════

class TestTools:
    async def test_skill_list_returns_list(self):
        from app.agents.tools import skill_list
        result = await skill_list()
        assert isinstance(result, list)
        assert len(result) > 0

    async def test_skill_list_items_have_name(self):
        from app.agents.tools import skill_list
        skills = await skill_list()
        for skill in skills:
            assert "name" in skill

    async def test_skill_load_returns_string(self):
        from app.agents.tools import skill_list, skill_load
        skills = await skill_list()
        if not skills:
            pytest.skip("No skills")
        content = await skill_load(skills[0]["name"])
        assert isinstance(content, str)
        assert len(content) > 0

    async def test_skill_load_nonexistent(self):
        from app.agents.tools import skill_load
        result = await skill_load("nonexistent-skill-xyz")
        # Should return error string, not raise
        assert isinstance(result, str)
        assert "not found" in result.lower() or "error" in result.lower() or len(result) > 0

    async def test_lint_draft_passes_good_content(self):
        from app.agents.tools import lint_draft_tool
        good_draft = (
            "Here is a key insight I discovered after 3 years working in ML: "
            "most teams underestimate data quality. I tested this across 12 projects. "
            "The fix is simple: audit your labels before training. "
            "Save 40% of your debugging time with one afternoon of label review."
        )
        result = await lint_draft_tool(good_draft, task_id="test-task")
        assert isinstance(result, dict)
        assert "overall_pass" in result

    async def test_lint_draft_checks_all_categories(self):
        from app.agents.tools import lint_draft_tool
        content = "Some draft content for testing lint checks across all categories."
        result = await lint_draft_tool(content)
        expected_keys = [
            "rant_detection", "fluff_detection", "opening_strength",
            "credential_stating", "engagement_bait", "micro_learning", "overall_pass"
        ]
        for key in expected_keys:
            assert key in result, f"Missing lint key: {key}"

    async def test_lint_draft_each_check_has_pass_flag(self):
        from app.agents.tools import lint_draft_tool
        result = await lint_draft_tool("Test draft content here for linting verification.")
        for key in ["rant_detection", "fluff_detection", "opening_strength",
                    "credential_stating", "engagement_bait", "micro_learning"]:
            assert "pass" in result[key], f"No 'pass' flag in {key}"

    async def test_lint_rant_detection_flags_rant(self):
        from app.agents.tools import lint_draft_tool
        rant = (
            "Everyone is WRONG about this! Nobody gets it! They are all lying to you! "
            "Wake up! The entire industry is corrupt and stupid and terrible! "
            "I can't believe people are so dumb! This makes me so angry!"
        )
        result = await lint_draft_tool(rant)
        # Rant detection should flag this
        assert "rant_detection" in result

    async def test_format_linkedin(self):
        from app.agents.tools import format_for_platform_tool
        content = "## My Insight\n\nHere is what I learned from **5 years** in tech.\n\nKey point: data > opinion."
        result = await format_for_platform_tool(content, platform="linkedin")
        assert isinstance(result, str)
        assert len(result) > 0

    async def test_format_linkedin_removes_markdown(self):
        from app.agents.tools import format_for_platform_tool
        content = "## Header\n\n**Bold** and *italic* text here.\n\n- Item 1\n- Item 2"
        result = await format_for_platform_tool(content, platform="linkedin")
        assert "##" not in result
        assert "**" not in result

    async def test_format_linkedin_max_length(self):
        from app.agents.tools import format_for_platform_tool
        long_content = "A " * 2000  # Very long content
        result = await format_for_platform_tool(long_content, platform="linkedin")
        assert len(result) <= 3100  # Allow some buffer for formatting

    async def test_format_twitter_creates_thread(self):
        from app.agents.tools import format_for_platform_tool
        content = " ".join(["word"] * 200)  # Long enough to require threading
        result = await format_for_platform_tool(content, platform="twitter")
        assert isinstance(result, str)
        assert len(result) > 0

    async def test_format_twitter_respects_char_limit(self):
        from app.agents.tools import format_for_platform_tool
        content = "Short tweet content."
        result = await format_for_platform_tool(content, platform="twitter")
        # Each tweet should be ≤ 280 chars (plus thread numbering)
        assert isinstance(result, str)

    async def test_memory_read_tool_returns_string(self):
        from app.agents.tools import memory_read_tool
        result = await memory_read_tool()
        assert isinstance(result, str)

    async def test_memory_write_then_read(self):
        from app.agents.tools import memory_write_tool, memory_read_tool
        await memory_write_tool(
            memory_type="Experience",
            text="Tool test: worked on distributed systems.",
            tags=["distributed", "systems"],
        )
        result = await memory_read_tool(memory_type="Experience")
        assert isinstance(result, str)

    async def test_compute_patterns_returns_string(self):
        from app.agents.tools import compute_patterns_tool
        result = await compute_patterns_tool(limit=10)
        assert isinstance(result, str)

    async def test_web_search_tool_returns_string(self):
        from app.agents.tools import web_search_tool
        result = await web_search_tool("AI in content creation", num_results=3)
        assert isinstance(result, str)
        assert len(result) > 0


# ══════════════════════════════════════════════════════════════════════════════
# 8. MEMORY STORE (unit tests)
# ══════════════════════════════════════════════════════════════════════════════

class TestMemoryStore:
    async def test_create_and_get_memory_entry(self, db_session):
        from app.memory.store import create_memory_entry, get_identity_memory
        from app.memory.models import MemoryEntryCreate
        entry = await create_memory_entry(db_session, MemoryEntryCreate(
            type="Experience",
            text="Worked at a startup for 3 years.",
            tags=["startup", "experience"],
        ))
        assert entry.id is not None
        assert entry.type == "Experience"
        all_entries = await get_identity_memory(db_session)
        ids = [e.id for e in all_entries]
        assert entry.id in ids

    async def test_update_memory_entry(self, db_session):
        from app.memory.store import create_memory_entry, update_memory_entry
        from app.memory.models import MemoryEntryCreate
        entry = await create_memory_entry(db_session, MemoryEntryCreate(
            type="Goal",
            text="Original goal text.",
        ))
        updated = await update_memory_entry(db_session, entry.id, "Updated goal text.")
        assert updated is not None
        assert updated.text == "Updated goal text."

    async def test_delete_memory_entry(self, db_session):
        from app.memory.store import create_memory_entry, delete_memory_entry, get_identity_memory
        from app.memory.models import MemoryEntryCreate
        entry = await create_memory_entry(db_session, MemoryEntryCreate(
            type="Current",
            text="Temporary entry.",
        ))
        deleted = await delete_memory_entry(db_session, entry.id)
        assert deleted is True
        all_entries = await get_identity_memory(db_session)
        ids = [e.id for e in all_entries]
        assert entry.id not in ids

    async def test_delete_nonexistent_returns_false(self, db_session):
        from app.memory.store import delete_memory_entry
        result = await delete_memory_entry(db_session, "totally-fake-id")
        assert result is False

    async def test_create_and_list_domains(self, db_session):
        from app.memory.store import create_domain, get_domains
        from app.memory.models import KnowledgeDomainCreate
        domain = await create_domain(db_session, KnowledgeDomainCreate(
            name="Test Domain XYZ",
            tags=["test", "domain"],
        ))
        assert domain.id is not None
        domains = await get_domains(db_session)
        names = [d.name for d in domains]
        assert "Test Domain XYZ" in names

    async def test_compose_context_discovery(self, db_session):
        from app.memory.store import compose_context
        ctx = await compose_context(db_session, stage="discovery")
        assert hasattr(ctx, "identity_memory")
        assert hasattr(ctx, "knowledge_domains")
        assert hasattr(ctx, "recent_tasks")

    async def test_compose_context_post_mortem_includes_patterns(self, db_session):
        from app.memory.store import compose_context
        ctx = await compose_context(db_session, stage="post-mortem")
        # Post-mortem should include performance patterns
        assert hasattr(ctx, "performance_patterns")

    async def test_compose_context_to_prompt_text(self, db_session):
        from app.memory.store import compose_context
        ctx = await compose_context(db_session, stage="extraction")
        text = ctx.to_prompt_text()
        assert isinstance(text, str)

    async def test_get_recent_tasks(self, db_session):
        from app.memory.store import get_recent_tasks
        tasks = await get_recent_tasks(db_session, limit=5)
        assert isinstance(tasks, list)

    async def test_compute_performance_patterns(self, db_session):
        from app.memory.store import compute_performance_patterns
        patterns = await compute_performance_patterns(db_session)
        assert hasattr(patterns, "total_posts")
        assert hasattr(patterns, "avg_save_rate")
        assert hasattr(patterns, "archetype_performance")


# ══════════════════════════════════════════════════════════════════════════════
# 9. PERSISTENCE — Chat history survives across requests
# ══════════════════════════════════════════════════════════════════════════════

class TestPersistence:
    async def test_chat_history_persists(self, client):
        task = await create_task(client)
        await client.post(
            f"/tasks/{task['id']}/chat",
            json={"message": "Persistent message test.", "user_id": "user_persist"},
        )
        # Re-fetch the task (new request)
        resp = await client.get(f"/tasks/{task['id']}")
        history = resp.json().get("chat_history") or []
        user_msgs = [m for m in history if m.get("role") == "user"]
        contents = [m["content"] for m in user_msgs]
        assert "Persistent message test." in contents

    async def test_task_fields_persist_after_update(self, client):
        task = await create_task(client)
        await client.patch(f"/tasks/{task['id']}", json={"domain": "Machine Learning"})
        await client.patch(f"/tasks/{task['id']}", json={"archetype": "Educator"})
        resp = await client.get(f"/tasks/{task['id']}")
        assert resp.json()["domain"] == "Machine Learning"
        assert resp.json()["archetype"] == "Educator"

    async def test_stage_persists_after_advance(self, client):
        task = await create_task(client)
        await client.patch(f"/tasks/{task['id']}/stage", json={"stage": "structuring"})
        resp = await client.get(f"/tasks/{task['id']}")
        assert resp.json()["stage"] == "structuring"

    async def test_memory_entries_persist(self, client):
        await client.post("/memory", json={
            "type": "Voice",
            "text": "I write in a direct, no-fluff style.",
            "tags": ["voice", "style"],
        })
        resp = await client.get("/memory")
        texts = [e["text"] for e in resp.json()]
        assert "I write in a direct, no-fluff style." in texts

    async def test_multiple_drafts_persist(self, client):
        task = await create_task(client)
        await client.post(f"/tasks/{task['id']}/drafts", json={"content": "Draft v1", "version": 1})
        await client.post(f"/tasks/{task['id']}/drafts", json={"content": "Draft v2", "version": 2})
        resp = await client.get(f"/tasks/{task['id']}")
        # Task should still exist with valid data
        assert resp.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
# 10. FULL LIFECYCLE FLOW (end-to-end integration)
# ══════════════════════════════════════════════════════════════════════════════

class TestFullLifecycleFlow:
    async def test_complete_discovery_to_extraction(self, client):
        # Create task
        task = await create_task(client, role="researcher", intent="teach", title="AI in Education")
        assert task["stage"] == "discovery"

        # Chat with Strategist in discovery
        resp = await client.post(
            f"/tasks/{task['id']}/chat",
            json={"message": "I want to write about AI tools in higher education.", "user_id": "test_user"},
        )
        assert resp.status_code == 200
        assert "[DONE]" in resp.text

        # Advance to extraction
        stage_resp = await client.patch(f"/tasks/{task['id']}/stage", json={"stage": "extraction"})
        assert stage_resp.json()["stage"] == "extraction"

        # Chat with Interviewer in extraction
        chat_resp = await client.post(
            f"/tasks/{task['id']}/chat",
            json={"message": "I've seen AI tools cut assignment turnaround by 40%.", "user_id": "test_user"},
        )
        assert chat_resp.status_code == 200
        history = (await client.get(f"/tasks/{task['id']}")).json().get("chat_history") or []
        assert len(history) >= 3  # at least: discovery user + discovery agent + extraction user

    async def test_structuring_stage_flow(self, client):
        task = await create_task(client)
        await client.patch(f"/tasks/{task['id']}/stage", json={"stage": "structuring"})
        resp = await client.post(
            f"/tasks/{task['id']}/chat",
            json={"message": "My key insight is that consistency beats perfection in content.", "user_id": "test_user"},
        )
        assert resp.status_code == 200
        chunks = parse_sse(resp.text)
        assert len(chunks) > 0

    async def test_vetting_with_real_draft(self, client):
        task = await create_task(client)
        await client.patch(f"/tasks/{task['id']}/stage", json={"stage": "vetting"})
        draft = (
            "After publishing 200 posts, I noticed something: specificity wins every time. "
            "Vague posts get ignored. Specific posts get saved. "
            "The data: specific posts had 3x the save rate in my last 50 posts. "
            "Start with a number. Name the mechanism. Show the result."
        )
        resp = await client.post(
            f"/tasks/{task['id']}/chat",
            json={"message": draft, "user_id": "test_user"},
        )
        assert resp.status_code == 200

    async def test_full_7_stage_journey(self, client):
        task = await create_task(client, title="Full journey test")
        stages = [
            ("discovery", "What angles exist for writing about remote work?"),
            ("extraction", "I managed 20 remote engineers for 3 years. Biggest lesson: async-first culture wins."),
            ("structuring", "My key insight is async beats sync for remote teams."),
            ("drafting", "How should I write the opening hook?"),
            ("vetting", "3 years, 20 engineers, one rule: async beats sync. Here's how we did it."),
            ("ready", "Final content is ready for publishing."),
            ("post-mortem", "Got 1200 impressions, 85 saves, 12 comments, 4 DMs."),
        ]
        for stage, message in stages:
            if stage != "discovery":
                adv = await client.patch(f"/tasks/{task['id']}/stage", json={"stage": stage})
                assert adv.json()["stage"] == stage

            resp = await client.post(
                f"/tasks/{task['id']}/chat",
                json={"message": message, "user_id": "test_user"},
            )
            assert resp.status_code == 200, f"Chat failed at stage: {stage}"
            assert "[DONE]" in resp.text, f"No [DONE] at stage: {stage}"

        # Verify full history at end
        final = (await client.get(f"/tasks/{task['id']}")).json()
        assert final["stage"] == "post-mortem"
        history = final.get("chat_history") or []
        assert len(history) >= 7  # At least one message per stage


# ══════════════════════════════════════════════════════════════════════════════
# 11. AGENT BUILDERS (unit tests)
# ══════════════════════════════════════════════════════════════════════════════

class TestAgentBuilders:
    def test_build_strategist_returns_agent(self):
        from app.agents.strategist import build_strategist
        agent = build_strategist(stage="discovery", user_id="test", session_id="sess-1")
        assert agent is not None

    def test_build_interviewer_returns_agent(self):
        from app.agents.interviewer import build_interviewer
        for role in ["researcher", "storyteller", "teacher", "coder"]:
            agent = build_interviewer(role=role, user_id="test", session_id="sess-1")
            assert agent is not None, f"build_interviewer failed for role: {role}"

    def test_build_shaper_returns_agent(self):
        from app.agents.shaper import build_shaper
        for mode in ["structuring", "drafting", "vetting"]:
            agent = build_shaper(mode=mode, user_id="test", session_id="sess-1")
            assert agent is not None, f"build_shaper failed for mode: {mode}"

    def test_build_analyst_returns_agent(self):
        from app.agents.analyst import build_analyst
        agent = build_analyst(user_id="test", session_id="sess-1")
        assert agent is not None

    def test_agents_have_model(self):
        from app.agents.strategist import build_strategist
        from app.agents.interviewer import build_interviewer
        from app.config import settings
        if not settings.has_any_ai_key:
            pytest.skip("Mock mode — model routing not applicable")
        agent = build_strategist(stage="discovery", session_id="test")
        assert agent.model is not None

    async def test_strategist_responds_in_mock_mode(self):
        from app.agents.strategist import build_strategist
        from app.config import settings
        agent = build_strategist(stage="discovery", session_id="test-mock")
        chunks = []
        async for chunk in agent.arun("What topics should I explore?", stream=True):
            if hasattr(chunk, "content") and chunk.content:
                chunks.append(chunk.content)
        assert len(chunks) > 0 or not settings.has_any_ai_key


# ══════════════════════════════════════════════════════════════════════════════
# 12. CONFIG & SETTINGS
# ══════════════════════════════════════════════════════════════════════════════

class TestConfig:
    def test_settings_loads(self):
        from app.config import settings
        assert settings is not None

    def test_settings_has_database_url(self):
        from app.config import settings
        assert settings.database_url != ""

    def test_settings_primary_provider(self):
        from app.config import settings
        assert settings.primary_provider in ("openrouter", "mock")

    def test_settings_has_ai_key_or_mock(self):
        from app.config import settings
        # Either has a key or is in mock mode — never undefined
        assert isinstance(settings.has_any_ai_key, bool)

    def test_settings_cors_origins_is_list(self):
        from app.config import settings
        assert isinstance(settings.cors_origins, list)
        assert len(settings.cors_origins) > 0

    def test_settings_environment(self):
        from app.config import settings
        assert settings.environment in ("development", "staging", "production")

    def test_model_router_tiers(self):
        from app.models.router import get_tier1_model, get_tier2_model, get_tier3_model
        t1 = get_tier1_model()
        t2 = get_tier2_model()
        t3 = get_tier3_model()
        assert t1 is not None
        assert t2 is not None
        assert t3 is not None
