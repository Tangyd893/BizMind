"""Agent chat service — LangGraph orchestration with SSE streaming.

P2: full LangGraph agent with Router → Retrieve → Grade → Rewrite → Generate → Critique.
"""

import json
import time
from collections.abc import AsyncIterator

from app.agent.graph import build_agent_graph
from app.models import MessageRole, User
from app.services.thread_service import save_message


async def stream_agent_chat(
    user: User,
    thread_id: str,
    message: str,
) -> AsyncIterator[str]:
    """Run the LangGraph agent and yield SSE events.

    Events:
      - event: agent_step → data: {"node": "...", "status": "..."}
      - event: token → data: {"content": "..."}
      - event: citation → data: {...}
      - event: done → data: {"message_id": "...", ...}
      - event: error → data: {"code": "...", "message": "..."}
    """
    from app.db.session import AsyncSessionLocal

    latency_start = time.perf_counter()

    try:
        # 1. Save user message
        async with AsyncSessionLocal() as session:
            await save_message(session, thread_id, MessageRole.USER, message)

        # 2. Build initial state
        initial_state = {
            "query": message,
            "rewritten_query": None,
            "retrieved_chunks": [],
            "retrieval_score": 0.0,
            "retrieval_attempts": 0,
            "generation": "",
            "critique_passed": False,
            "critique_feedback": None,
            "citations": [],
            "route": "rag",
            "tenant_id": str(user.tenant_id),
            "thread_id": thread_id,
            "web_search_results": None,
        }

        # 3. Run graph with streaming
        graph = build_agent_graph()
        full_response = ""
        final_state = {}

        async for event in graph.astream(initial_state, stream_mode="updates"):
            for node_name, node_output in event.items():
                # Emit agent_step
                yield _sse_event("agent_step", {
                    "node": node_name,
                    "status": "completed",
                })

                # Capture output
                if node_name in ("generate", "direct_answer", "oos_answer"):
                    if "generation" in node_output:
                        full_response = node_output["generation"]
                        # Stream tokens one by one for smooth UI
                        words = full_response.split(" ")
                        for i, word in enumerate(words):
                            sep = " " if i > 0 else ""
                            yield _sse_event("token", {"content": sep + word})

                    if "citations" in node_output and node_output["citations"]:
                        for citation in node_output["citations"]:
                            yield _sse_event("citation", citation)

                final_state.update(node_output)

        # If no generation happened (e.g., graph ended without hitting generate)
        if not full_response and "generation" in final_state:
            full_response = final_state["generation"]
            if full_response:
                yield _sse_event("token", {"content": full_response})

        # 4. Save assistant message
        latency_ms = int((time.perf_counter() - latency_start) * 1000)
        citations = final_state.get("citations", [])

        async with AsyncSessionLocal() as session:
            saved_msg = await save_message(
                session,
                thread_id,
                MessageRole.ASSISTANT,
                full_response or "(no response)",
                citations=citations,
                latency_ms=latency_ms,
            )

        # 5. Done
        yield _sse_event("done", {
            "message_id": str(saved_msg.id),
            "route": final_state.get("route", "rag"),
            "retrieval_attempts": final_state.get("retrieval_attempts", 0),
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
