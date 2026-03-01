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
from app.db.models import CoddeTask

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

                buf += chunk
                segments, buf, in_thinking = _drain(buf, in_thinking)

                for seg_type, text in segments:
                    if not text:
                        continue
                    escaped = text.replace("\n", "\\n")
                    if seg_type == "thinking":
                        yield f"event: thinking\ndata: {escaped}\n\n"
                    else:
                        clean_message += text
                        yield f"data: {escaped}\n\n"

            # Flush remaining buffer
            if buf:
                escaped = buf.replace("\n", "\\n")
                if in_thinking:
                    yield f"event: thinking\ndata: {escaped}\n\n"
                else:
                    clean_message += buf
                    yield f"data: {escaped}\n\n"

            # ── Save clean chat history (no thinking tags) ─────────────────
            history = list(task.chat_history or [])
            if not body.message.startswith("[AUTO_OPEN]"):
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
            async with AsyncSessionLocal() as session:
                db_task = await session.get(CoddeTask, task_id)
                if db_task:
                    db_task.chat_history = history
                    await session.commit()

        except Exception as e:
            logger.error(f"Stream error on task {task_id}: {str(e)}", exc_info=True)
            yield f"data: [AgentOS Error: {str(e)}]\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
