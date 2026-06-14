"""Router node — classify intent."""

from app.rag.llm_client import get_llm_client


def _load_prompt(name: str) -> str:
    from pathlib import Path
    path = Path(__file__).parent.parent / "prompts" / name
    return path.read_text(encoding="utf-8")


ROUTER_SYSTEM = _load_prompt("router.system.txt")


async def router_node(state: dict) -> dict:
    """Classify the user's intent: rag, direct, web, or oos."""
    query = state["query"]
    llm = get_llm_client()

    messages = [
        {"role": "system", "content": ROUTER_SYSTEM},
        {"role": "user", "content": query},
    ]

    # Collect full response (non-streaming for classification)
    response = ""
    async for token in llm.chat_stream(messages, temperature=0.0, max_tokens=10):
        response += token

    route = response.strip().lower()
    if route not in ("rag", "direct", "web", "oos"):
        route = "rag"  # default fallback

    return {"route": route}
