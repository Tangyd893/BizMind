"""Rewrite node — improve query for better retrieval."""

from app.rag.llm_client import get_llm_client


def _load_prompt(name: str) -> str:
    from pathlib import Path
    path = Path(__file__).parent.parent / "prompts" / name
    return path.read_text(encoding="utf-8")


REWRITE_SYSTEM = _load_prompt("rewrite.system.txt")


async def rewrite_node(state: dict) -> dict:
    """Rewrite the query to improve retrieval precision."""
    original = state.get("rewritten_query") or state["query"]

    llm = get_llm_client()
    response = ""
    async for token in llm.chat_stream(
        [{"role": "system", "content": REWRITE_SYSTEM}, {"role": "user", "content": original}],
        temperature=0.3,
        max_tokens=200,
    ):
        response += token

    rewritten = response.strip() or original
    return {"rewritten_query": rewritten}
