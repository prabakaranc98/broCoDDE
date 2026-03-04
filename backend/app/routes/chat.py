"""
BroCoDDE — SSE Streaming Chat Route
POST /tasks/{id}/chat → Server-Sent Events streaming agent response

Thinking tag handling:
- Claude models may emit <thinking>...</thinking> or <anthropic:thinking>...</anthropic:thinking>
  blocks in the content stream. These are separated and sent as `event: thinking` SSE frames
  so the frontend can render them distinctly (frontier-chatbot style) without polluting
  the chat history saved to the database.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.harness import stream_chat
from app.db.database import get_db
from app.db.models import CoddeTask, Series

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    user_id: str = "default_user"
    deep_critique: bool = False


# ── Thinking tag helpers ───────────────────────────────────────────────────────

# Ordered by priority — longer/more-specific tags first so they match before the short form
_THINK_OPEN_TAGS = ["<anthropic:thinking>", "<thinking>"]
_THINK_CLOSE_TAGS = ["</anthropic:thinking>", "</thinking>"]
_MAX_TAG_LEN = max(len(t) for t in _THINK_OPEN_TAGS + _THINK_CLOSE_TAGS)


def _find_open(text: str) -> tuple[int, int]:
    """Return (start, end_of_tag) for the first thinking open tag, or (-1, -1)."""
    best = len(text)
    result = (-1, -1)
    for tag in _THINK_OPEN_TAGS:
        idx = text.find(tag)
        if idx != -1 and idx < best:
            best = idx
            result = (idx, idx + len(tag))
    return result


def _find_close(text: str) -> tuple[int, int]:
    """Return (start, end_of_tag) for the first thinking close tag, or (-1, -1)."""
    best = len(text)
    result = (-1, -1)
    for tag in _THINK_CLOSE_TAGS:
        idx = text.find(tag)
        if idx != -1 and idx < best:
            best = idx
            result = (idx, idx + len(tag))
    return result


def _drain(buf: str, in_thinking: bool) -> tuple[list[tuple[str, str]], str, bool]:
    """
    Process `buf` and split content at thinking tag boundaries.

    Returns:
        segments: list of ("thinking" | "message", text)
        remaining: unprocessed buffer (potential partial tag at end)
        in_thinking: updated state
    """
    segments: list[tuple[str, str]] = []

    while buf:
        if not in_thinking:
            open_start, open_end = _find_open(buf)
            if open_start == -1:
                # No open tag — hold back _MAX_TAG_LEN-1 chars in case of partial tag
                safe = max(0, len(buf) - _MAX_TAG_LEN + 1)
                if safe:
                    segments.append(("message", buf[:safe]))
                    buf = buf[safe:]
                break
            else:
                if open_start > 0:
                    segments.append(("message", buf[:open_start]))
                buf = buf[open_end:]
                in_thinking = True
        else:
            close_start, close_end = _find_close(buf)
            if close_start == -1:
                safe = max(0, len(buf) - _MAX_TAG_LEN + 1)
                if safe:
                    segments.append(("thinking", buf[:safe]))
                    buf = buf[safe:]
                break
            else:
                if close_start > 0:
                    segments.append(("thinking", buf[:close_start]))
                buf = buf[close_end:]
                in_thinking = False

    return segments, buf, in_thinking


# ── Route ─────────────────────────────────────────────────────────────────────

@router.post("/{task_id}/chat")
async def chat(
    task_id: str,
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Stream a chat response for the given CoDDE-task.
    Thinking blocks are emitted as `event: thinking` SSE frames and NOT saved to history.
    Regular content is emitted as default `data:` SSE frames and saved to history.
    """
    task = await db.get(CoddeTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    async def event_generator():
        from app.logger import logger
        from datetime import datetime

        yield "data: \n\n"  # SSE: open connection

        agent_role = task.role or "researcher"

        # Thinking parser state
        buf = ""
        in_thinking = False
        clean_message = ""  # non-thinking content — this is what gets saved to history

        should_advance = False

        try:
            async for chunk in stream_chat(
                message=body.message,
                task_stage=task.stage,
                task_id=task_id,
                role=agent_role,
                intent=task.intent or "teach",
                user_id=body.user_id,
                session_id=task_id,
                deep_critique=body.deep_critique,
            ):
                if not chunk:
                    continue

                # Fast-path: harness yields [TOOL:name] as a complete standalone chunk.
                # Intercept here before the drain buffer can split the marker mid-token.
                if chunk.startswith("[TOOL:") and chunk.endswith("]") and "\n" not in chunk:
                    yield f"event: tool\ndata: {chunk[6:-1]}\n\n"
                    continue

                buf += chunk
                segments, buf, in_thinking = _drain(buf, in_thinking)

                for seg_type, text in segments:
                    if not text:
                        continue
                    if seg_type == "message" and "[ADVANCE_STAGE]" in text:
                        text = text.replace("[ADVANCE_STAGE]", "")
                        should_advance = True
                        if not text.strip():
                            continue
                    # Intercept [TOOL:name] markers — emit as dedicated SSE event, not content
                    import re as _re_tool
                    if seg_type == "message":
                        tool_markers = _re_tool.findall(r'\[TOOL:([^\]]+)\]', text)
                        if tool_markers:
                            for tool_name in tool_markers:
                                yield f"event: tool\ndata: {tool_name}\n\n"
                            text = _re_tool.sub(r'\[TOOL:[^\]]+\]', '', text)
                            if not text.strip():
                                continue
                    escaped = text.replace("\n", "\\n")
                    if seg_type == "thinking":
                        yield f"event: thinking\ndata: {escaped}\n\n"
                    else:
                        clean_message += text
                        yield f"data: {escaped}\n\n"

            # Flush remaining buffer
            if buf:
                if in_thinking:
                    escaped = buf.replace("\n", "\\n")
                    yield f"event: thinking\ndata: {escaped}\n\n"
                else:
                    import re as _re_flush
                    if "[ADVANCE_STAGE]" in buf:
                        buf = buf.replace("[ADVANCE_STAGE]", "").strip()
                        should_advance = True
                    # Strip any [TOOL:...] markers that ended up in the flush buffer
                    buf = _re_flush.sub(r'\[TOOL:[^\]]+\]', '', buf).strip()
                    if buf:
                        escaped = buf.replace("\n", "\\n")
                        clean_message += buf
                        yield f"data: {escaped}\n\n"

            # ── Strip macros from clean_message before saving ──
            import re as _re
            # Safety net: catch [ADVANCE_STAGE] if split across chunks
            if "[ADVANCE_STAGE]" in clean_message:
                should_advance = True
                clean_message = clean_message.replace("[ADVANCE_STAGE]", "").strip()
            clean_message = _re.sub(r'\s*\[TITLE:[^\]]+\]\s*', ' ', clean_message).strip()
            clean_message = _re.sub(r'\s*\[TOOL:[^\]]+\]\s*', '', clean_message).strip()

            # ── Save clean chat history (no thinking tags) ─────────────────
            history = list(task.chat_history or [])
            is_auto_msg = body.message.startswith("[AUTO_OPEN]") or body.message.startswith("[AUTO_SPARK]")
            if not is_auto_msg:
                history.append({
                    "id": f"msg_u_{datetime.utcnow().timestamp()}",
                    "role": "user",
                    "content": body.message,
                    "timestamp": datetime.utcnow().isoformat(),
                })
            history.append({
                "id": f"msg_a_{datetime.utcnow().timestamp()}",
                "role": "agent",
                "content": clean_message,
                "timestamp": datetime.utcnow().isoformat(),
            })

            from app.db.database import AsyncSessionLocal
            auto_title: str | None = None
            async with AsyncSessionLocal() as session:
                db_task = await session.get(CoddeTask, task_id)
                if db_task:
                    db_task.chat_history = history
                    # ── Auto-derive title from first real user message ──────────────
                    # Only fires when title is still blank/Untitled and this is a real message
                    current_title = (db_task.title or "").strip()
                    is_real_msg = not is_auto_msg and body.message.strip()
                    if is_real_msg and current_title.lower() in ("", "untitled"):
                        raw = body.message.strip()
                        # Truncate at word boundary ≤ 60 chars
                        if len(raw) > 60:
                            raw = raw[:60].rsplit(" ", 1)[0]
                        derived = raw.strip(".,!?—:").strip()
                        if derived:
                            db_task.title = derived
                            auto_title = derived

                    # ── Auto-assign to series by domain ────────────────────────────
                    # If task has a domain but no series, find a series whose name
                    # overlaps with the domain string (case-insensitive substring).
                    if not db_task.series_id and db_task.domain:
                        from sqlalchemy import select as _select
                        domain_lc = db_task.domain.lower()
                        series_rows = await session.execute(_select(Series))
                        for s in series_rows.scalars().all():
                            s_lc = s.name.lower()
                            if domain_lc in s_lc or s_lc in domain_lc:
                                db_task.series_id = s.id
                                break

                    await session.commit()

        except Exception as e:
            logger.error(f"Stream error on task {task_id}: {str(e)}", exc_info=True)
            yield f"data: [AgentOS Error: {str(e)}]\n\n"

        # Emit title update event so the sidebar/header refresh without a reload
        if auto_title:
            escaped_title = auto_title.replace("\n", " ")
            yield f"event: title\ndata: {escaped_title}\n\n"

        # Emit stage advance event BEFORE [DONE] so frontend processes it first
        if should_advance:
            yield "event: advance\ndata: next\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
