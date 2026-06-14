"""Chat endpoints — SSE streaming for baseline and agent chat."""

from app.dependencies import get_current_user
from app.models import User
from app.schemas.chat import ChatRequest
from app.services.agent_chat_service import stream_agent_chat
from app.services.chat_service import stream_chat
from fastapi import APIRouter, Depends
from starlette.responses import StreamingResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/baseline/stream")
async def baseline_chat_stream(
    req: ChatRequest,
    user: User = Depends(get_current_user),
) -> StreamingResponse:
    """Stream a baseline RAG response via SSE."""
    return StreamingResponse(
        stream_chat(user, req.thread_id, req.message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/stream")
async def agent_chat_stream(
    req: ChatRequest,
    user: User = Depends(get_current_user),
) -> StreamingResponse:
    """Stream an agentic RAG response via SSE with agent_step events."""
    return StreamingResponse(
        stream_agent_chat(user, req.thread_id, req.message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
