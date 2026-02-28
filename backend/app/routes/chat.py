"""
BroCoDDE — SSE Streaming Chat Route
POST /tasks/{id}/chat → Server-Sent Events streaming agent response
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


@router.post("/{task_id}/chat")
async def chat(
    task_id: str,
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Stream a chat response for the given CoDDE-task.
    The harness routes to the correct agent based on the task's current stage.
    Response is Server-Sent Events (SSE) — each chunk is `data: <text>\n\n`.
    """
    task = await db.get(CoddeTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    async def event_generator():
        from app.logger import logger
        yield "data: \n\n"  # SSE: open connection
        
        try:
            async for chunk in stream_chat(
                message=body.message,
                task_stage=task.stage,
                task_id=task_id,
                role=task.role or "researcher",
                intent=task.intent or "teach",
                user_id=body.user_id,
                session_id=f"{task_id}-{task.stage}",
                deep_critique=body.deep_critique,
            ):
                if chunk:
                    # Escape newlines in SSE data field
                    escaped = chunk.replace("\n", "\\n")
                    yield f"data: {escaped}\n\n"
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
