"""LangGraph agent graph builder.

Assembles the full agent workflow:
  router → direct_answer / retrieve / web_search / oos_answer
  retrieve → grade
  grade → generate / rewrite
  rewrite → retrieve / web_search
  generate → critique
  critique → END / generate
"""

from langgraph.graph import END, StateGraph

from app.agent.nodes.critique import critique_node
from app.agent.nodes.generate import generate_node
from app.agent.nodes.grade import grade_node
from app.agent.nodes.retrieve import retrieve_node
from app.agent.nodes.rewrite import rewrite_node
from app.agent.nodes.router import router_node
from app.agent.nodes.web_search import web_search_node
from app.agent.state import AgentState
from app.config import get_settings


def _route_after_router(state: dict) -> str:
    route = state.get("route", "rag")
    return {
        "direct": "direct_answer",
        "rag": "retrieve",
        "web": "web_search",
        "oos": "oos_answer",
    }.get(route, "retrieve")


def _route_after_grade(state: dict) -> str:
    chunks = state.get("retrieved_chunks", [])
    score = state.get("retrieval_score", 0.0)
    if not chunks:
        return "web_search" if state.get("web_search", True) else "generate"
    if score >= get_settings().grade_threshold:
        return "generate"
    return "rewrite"


def _route_after_rewrite(state: dict) -> str:
    settings = get_settings()
    if state.get("retrieval_attempts", 0) >= settings.max_retrieval_retries:
        return "web_search" if getattr(settings, "web_search_enabled", False) else "generate"
    return "retrieve"


def _route_after_critique(state: dict) -> str:
    if state.get("critique_passed", True):
        return END
    retries = state.get("_critique_retries", 0)
    if retries >= get_settings().max_critique_retries:
        return END
    state["_critique_retries"] = retries + 1
    return "generate"


async def _direct_answer_node(state: dict) -> dict:
    """Handle direct/greeting questions without retrieval."""
    query = state["query"]
    from app.rag.llm_client import get_llm_client

    def _load_prompt(name: str) -> str:
        from pathlib import Path
        path = Path(__file__).parent / "prompts" / name
        return path.read_text(encoding="utf-8")

    system = _load_prompt("generate.system.txt")

    llm = get_llm_client()
    response = ""
    async for token in llm.chat_stream(
        [{"role": "system", "content": system}, {"role": "user", "content": query}],
        temperature=0.3,
        max_tokens=512,
    ):
        response += token
    return {"generation": response, "citations": []}


async def _oos_answer_node(state: dict) -> dict:
    """Handle out-of-scope questions with a polite decline."""
    from app.rag.llm_client import get_llm_client

    def _load_prompt(name: str) -> str:
        from pathlib import Path
        path = Path(__file__).parent / "prompts" / name
        return path.read_text(encoding="utf-8")

    system = _load_prompt("oos.system.txt")

    llm = get_llm_client()
    response = ""
    async for token in llm.chat_stream(
        [{"role": "system", "content": system}, {"role": "user", "content": state["query"]}],
        temperature=0.3,
        max_tokens=200,
    ):
        response += token
    return {"generation": response, "citations": []}


def build_agent_graph() -> StateGraph:
    """Build and compile the LangGraph agent."""
    g = StateGraph(AgentState)

    # Nodes
    g.add_node("router", router_node)
    g.add_node("retrieve", retrieve_node)
    g.add_node("grade", grade_node)
    g.add_node("rewrite", rewrite_node)
    g.add_node("web_search", web_search_node)
    g.add_node("generate", generate_node)
    g.add_node("critique", critique_node)
    g.add_node("direct_answer", _direct_answer_node)
    g.add_node("oos_answer", _oos_answer_node)

    # Entry
    g.set_entry_point("router")

    # Edges
    g.add_conditional_edges("router", _route_after_router, {
        "direct_answer": "direct_answer",
        "retrieve": "retrieve",
        "web_search": "web_search",
        "oos_answer": "oos_answer",
    })
    g.add_edge("retrieve", "grade")
    g.add_conditional_edges("grade", _route_after_grade, {
        "generate": "generate",
        "rewrite": "rewrite",
        "web_search": "web_search",
    })
    g.add_conditional_edges("rewrite", _route_after_rewrite, {
        "retrieve": "retrieve",
        "web_search": "web_search",
        "generate": "generate",
    })
    g.add_edge("web_search", "generate")
    g.add_edge("generate", "critique")
    g.add_conditional_edges("critique", _route_after_critique, {
        END: END,
        "generate": "generate",
    })
    g.add_edge("direct_answer", END)
    g.add_edge("oos_answer", END)

    return g.compile()
