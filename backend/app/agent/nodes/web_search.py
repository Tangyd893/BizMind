"""Web search node — search the web for external information."""

from app.config import get_settings


async def web_search_node(state: dict) -> dict:
    """Search the web using Tavily (if configured)."""
    query = state.get("rewritten_query") or state["query"]
    settings = get_settings()

    tavily_key = getattr(settings, "tavily_api_key", "")
    if not tavily_key:
        return {"web_search_results": []}

    try:
        import httpx
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": tavily_key,
                    "query": query,
                    "search_depth": "basic",
                    "max_results": 5,
                },
            )
            response.raise_for_status()
            data = response.json()
            results = [
                {"url": r["url"], "content": r.get("content", "")}
                for r in data.get("results", [])
            ]
            return {"web_search_results": results}
    except Exception:
        return {"web_search_results": []}
