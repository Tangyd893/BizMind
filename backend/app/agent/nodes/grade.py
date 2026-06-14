"""Grade node — evaluate retrieval quality."""

import json

from app.rag.llm_client import get_llm_client


def _load_prompt(name: str) -> str:
    from pathlib import Path
    path = Path(__file__).parent.parent / "prompts" / name
    return path.read_text(encoding="utf-8")


GRADE_SYSTEM = _load_prompt("grade.system.txt")


async def grade_node(state: dict) -> dict:
    """Evaluate the relevance of retrieved chunks to the query."""
    query = state.get("rewritten_query") or state["query"]
    chunks = state.get("retrieved_chunks", [])

    if not chunks:
        return {"retrieval_score": 0.0}

    # Build chunk preview
    chunk_texts = []
    for i, c in enumerate(chunks[:10], 1):
        chunk_texts.append(f"[{i}] {c['source']}: {c['text'][:300]}")
    chunks_preview = "\n\n".join(chunk_texts)

    llm = get_llm_client()
    user_msg = f"Query: {query}\n\nRetrieved chunks:\n{chunks_preview}"

    response = ""
    async for token in llm.chat_stream(
        [{"role": "system", "content": GRADE_SYSTEM}, {"role": "user", "content": user_msg}],
        temperature=0.0,
        max_tokens=100,
    ):
        response += token

    try:
        result = json.loads(response)
        score = float(result.get("score", 0.0))
    except (json.JSONDecodeError, ValueError):
        score = 0.5  # default on parse failure

    return {"retrieval_score": score}
