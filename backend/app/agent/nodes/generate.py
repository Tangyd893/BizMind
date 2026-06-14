"""Generate node — produce an answer with citations."""

from app.rag.llm_client import get_llm_client


def _load_prompt(name: str) -> str:
    from pathlib import Path
    path = Path(__file__).parent.parent / "prompts" / name
    return path.read_text(encoding="utf-8")


GENERATE_SYSTEM = _load_prompt("generate.system.txt")


async def generate_node(state: dict, *, stream_callback=None) -> dict:
    """Generate an answer using retrieved context or web results.

    If stream_callback is provided, it will be called with each token
    for SSE streaming.
    """
    query = state.get("rewritten_query") or state["query"]
    chunks = state.get("retrieved_chunks", [])
    web_results = state.get("web_search_results") or []

    # Build context XML
    context_parts = []
    if chunks:
        for _i, c in enumerate(chunks, 1):
            context_parts.append(
                f'<chunk id="{c["chunk_id"]}" source="{c["source"]}" '
                f'page="{c.get("page") or ""}">\n{c["text"]}\n</chunk>'
            )
    if web_results:
        for i, w in enumerate(web_results, 1):
            context_parts.append(
                f'<web_result id="web-{i}" source="{w.get("url", "")}">\n'
                f'{w.get("content", "")}\n</web_result>'
            )

    context_xml = "\n".join(context_parts) if context_parts else "No context available."

    user_msg = f"""<retrieved_context>
{context_xml}
</retrieved_context>

<user_question>
{query}
</user_question>

Please answer based on the context above."""

    llm = get_llm_client()
    full_response = ""
    async for token in llm.chat_stream(
        [
            {"role": "system", "content": GENERATE_SYSTEM},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.1,
        max_tokens=2048,
    ):
        full_response += token
        if stream_callback:
            await stream_callback(token)

    # Build citations from chunks
    citations = [
        {
            "document_id": c["document_id"],
            "chunk_id": c["chunk_id"],
            "source": c["source"],
            "page": c.get("page"),
            "text_preview": c["text"][:200],
        }
        for c in (chunks or [])
    ]

    return {"generation": full_response, "citations": citations}
