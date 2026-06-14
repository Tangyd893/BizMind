"""Baseline chat service — retrieve → generate → stream SSE.

P1: single-round RAG with dense retrieval.
P2: LangGraph agent with multi-step reasoning.
"""

import json
import time
from collections.abc import AsyncIterator

from app.models import MessageRole, User
from app.rag.llm_client import get_llm_client
from app.rag.retriever import retrieve
from app.schemas.thread import Citation
from app.services.thread_service import save_message


def _build_prompt(query: str, context_chunks: list) -> str:
    """Build a RAG prompt with retrieved context."""
    context_parts = []
    for i, chunk in enumerate(context_chunks, 1):
        context_parts.append(f"[{i}] Source: {chunk.source}\n{chunk.text_preview}")

    context_text = "\n\n".join(context_parts)

    return (
        "You are a knowledgeable enterprise assistant. "
        "Answer the user's question based on the provided context.\n\n"
        "If the context does not contain enough information, say so honestly.\n"
        "Always cite sources when using information from the context.\n\n"
        f"## Context\n\n{context_text}\n\n"
        f"## Question\n\n{query}\n\n"
        f"## Answer\n"
    )


async def stream_chat(
    user: User,
    thread_id: str,
    message: str,
) -> AsyncIterator[str]:
    """Main baseline chat pipeline. Yields SSE-formatted strings.

    Events:
      - event: token  → data: {"content": "..."}
      - event: citation → data: {...}
      - event: done → data: {"message_id": "..."}
      - event: error → data: {"code": "...", "message": "..."}
    """
    from app.db.session import AsyncSessionLocal

    latency_start = time.perf_counter()

    try:
        # 1. Save user message
        async with AsyncSessionLocal() as session:
            await save_message(
                session, thread_id, MessageRole.USER, message
            )

        # 2. Retrieve
        tenant_id = str(user.tenant_id)
        retrieval = await retrieve(message, tenant_id)

        # Send citations
        citations = [
            Citation(
                document_id=c.document_id,
                chunk_id=c.chunk_id,
                source=c.source,
                page=c.page,
                text_preview=c.text_preview,
            )
            for c in retrieval.chunks
        ]
        for citation in citations:
            yield _sse_event("citation", citation.model_dump())

        # 3. Build prompt
        prompt = _build_prompt(message, retrieval.chunks)

        # 4. Stream LLM response
        llm = get_llm_client()
        full_response = ""
        async for token in llm.chat_stream(
            messages=[{"role": "user", "content": prompt}]
        ):
            full_response += token
            yield _sse_event("token", {"content": token})

        # 5. Save assistant message
        latency_ms = int((time.perf_counter() - latency_start) * 1000)

        async with AsyncSessionLocal() as session:
            saved_msg = await save_message(
                session,
                thread_id,
                MessageRole.ASSISTANT,
                full_response,
                citations=[c.model_dump() for c in citations],
                token_usage=None,  # Could parse from streaming response
                latency_ms=latency_ms,
            )

        # 6. Done
        yield _sse_event("done", {
            "message_id": str(saved_msg.id),
            "route": "baseline",
            "retrieval_latency_ms": int(retrieval.latency_ms),
            "total_latency_ms": latency_ms,
        })

    except Exception as exc:
        yield _sse_event("error", {
            "code": "INTERNAL_ERROR",
            "message": str(exc),
        })


def _sse_event(event: str, data: dict) -> str:
    """Format a Server-Sent Events message."""
    return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"
