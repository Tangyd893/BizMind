"""Critique node — self-check the generated answer."""

import json

from app.rag.llm_client import get_llm_client


def _load_prompt(name: str) -> str:
    from pathlib import Path
    path = Path(__file__).parent.parent / "prompts" / name
    return path.read_text(encoding="utf-8")


CRITIQUE_SYSTEM = _load_prompt("critique.system.txt")


async def critique_node(state: dict) -> dict:
    """Evaluate the generated answer for hallucinations and completeness."""
    query = state.get("rewritten_query") or state["query"]
    generation = state.get("generation", "")
    chunks = state.get("retrieved_chunks", [])

    if not generation:
        return {"critique_passed": True, "critique_feedback": None}

    # Build context summary
    context_text = "\n\n".join(
        f"[{i+1}] {c['source']}: {c['text'][:300]}" for i, c in enumerate(chunks[:10])
    )

    user_msg = f"""Question: {query}

Context:
{context_text}

Assistant Answer:
{generation}

Please evaluate the answer."""

    llm = get_llm_client()
    response = ""
    async for token in llm.chat_stream(
        [
            {"role": "system", "content": CRITIQUE_SYSTEM},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.0,
        max_tokens=200,
    ):
        response += token

    try:
        result = json.loads(response)
        passed = bool(result.get("passed", True))
        feedback = result.get("feedback")
    except (json.JSONDecodeError, ValueError):
        passed = True
        feedback = None

    return {"critique_passed": passed, "critique_feedback": feedback}
