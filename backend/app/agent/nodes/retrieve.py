"""Retrieve node — hybrid search."""

from app.rag.retriever import hybrid_retrieve


async def retrieve_node(state: dict) -> dict:
    """Retrieve relevant chunks using the hybrid retriever."""
    query = state.get("rewritten_query") or state["query"]
    tenant_id = state["tenant_id"]

    result = await hybrid_retrieve(query, tenant_id)

    return {
        "retrieved_chunks": [
            {
                "chunk_id": c.chunk_id,
                "document_id": c.document_id,
                "text": c.text_preview,
                "source": c.source,
                "page": c.page,
                "score": c.score,
            }
            for c in result.chunks
        ],
        "retrieval_attempts": state.get("retrieval_attempts", 0) + 1,
    }
