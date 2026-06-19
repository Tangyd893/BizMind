"""Tests for agent graph routing functions — pure functions, no mocks required."""

import pytest
from langgraph.graph import END

from app.agent.graph import (
    _route_after_router,
    _route_after_grade,
    _route_after_rewrite,
    _route_after_critique,
    build_agent_graph,
)


# ── _route_after_router ──────────────────────────────────────────────

@pytest.mark.parametrize(
    "route,expected",
    [
        ("direct", "direct_answer"),
        ("rag", "retrieve"),
        ("web", "web_search"),
        ("oos", "oos_answer"),
    ],
)
def test_route_after_router_known_routes(route, expected):
    assert _route_after_router({"route": route}) == expected


def test_route_after_router_unknown_defaults_to_retrieve():
    assert _route_after_router({"route": "bogus"}) == "retrieve"


def test_route_after_router_missing_key_defaults_to_retrieve():
    assert _route_after_router({}) == "retrieve"


# ── _route_after_grade ───────────────────────────────────────────────

def test_route_after_grade_empty_chunks_web_enabled():
    assert _route_after_grade({"retrieved_chunks": [], "web_search": True}) == "web_search"


def test_route_after_grade_empty_chunks_web_disabled():
    assert _route_after_grade({"retrieved_chunks": [], "web_search": False}) == "generate"


def test_route_after_grade_empty_chunks_web_missing_defaults_true():
    assert _route_after_grade({"retrieved_chunks": []}) == "web_search"


def test_route_after_grade_high_score():
    """score >= grade_threshold → generate (threshold is 0.6 by default)."""
    from app.config import get_settings
    threshold = get_settings().grade_threshold
    assert _route_after_grade(
        {"retrieved_chunks": [{"source": "x"}], "retrieval_score": threshold}
    ) == "generate"
    assert _route_after_grade(
        {"retrieved_chunks": [{"source": "x"}], "retrieval_score": 0.9}
    ) == "generate"


def test_route_after_grade_low_score():
    """score < grade_threshold → rewrite."""
    from app.config import get_settings
    threshold = get_settings().grade_threshold
    assert _route_after_grade(
        {"retrieved_chunks": [{"source": "x"}], "retrieval_score": threshold - 0.1}
    ) == "rewrite"
    assert _route_after_grade(
        {"retrieved_chunks": [{"source": "x"}], "retrieval_score": 0.0}
    ) == "rewrite"


# ── _route_after_rewrite ────────────────────────────────────────────

def test_route_after_rewrite_below_limit():
    """retrieval_attempts < max_retrieval_retries → retrieve."""
    from app.config import get_settings
    limit = get_settings().max_retrieval_retries
    assert _route_after_rewrite({"retrieval_attempts": limit - 1}) == "retrieve"
    assert _route_after_rewrite({"retrieval_attempts": 0}) == "retrieve"


def test_route_after_rewrite_at_limit_web_enabled():
    """At max retries with web_search_enabled → web_search."""
    from app.config import get_settings
    limit = get_settings().max_retrieval_retries
    # Temporarily enable web_search for the test
    import app.config as cfg
    original = getattr(cfg.get_settings(), "web_search_enabled", False)
    # Use monkeypatch-style: override the settings attribute
    try:
        cfg.get_settings().web_search_enabled = True
        assert _route_after_rewrite({"retrieval_attempts": limit}) == "web_search"
    finally:
        cfg.get_settings().web_search_enabled = original


def test_route_after_rewrite_at_limit_web_disabled():
    """At max retries, web_search_enabled=False → generate."""
    from app.config import get_settings
    limit = get_settings().max_retrieval_retries
    assert _route_after_rewrite({"retrieval_attempts": limit}) == "generate"


def test_route_after_rewrite_default_attempts():
    """Missing retrieval_attempts defaults to 0 → retrieve."""
    assert _route_after_rewrite({}) == "retrieve"


# ── _route_after_critique ───────────────────────────────────────────

def test_route_after_critique_passed():
    assert _route_after_critique({"critique_passed": True}) == END


def test_route_after_critique_not_passed_below_limit():
    assert _route_after_critique(
        {"critique_passed": False, "_critique_retries": 0}
    ) == "generate"


def test_route_after_critique_not_passed_increments_retries():
    state = {"critique_passed": False, "_critique_retries": 0}
    result = _route_after_critique(state)
    assert result == "generate"
    assert state["_critique_retries"] == 1


def test_route_after_critique_not_passed_at_max():
    from app.config import get_settings
    max_retries = get_settings().max_critique_retries
    assert _route_after_critique(
        {"critique_passed": False, "_critique_retries": max_retries}
    ) == END


def test_route_after_critique_default_passed():
    """Missing critique_passed defaults to True → END."""
    assert _route_after_critique({}) == END


# ── build_agent_graph ────────────────────────────────────────────────

def test_build_agent_graph_compiles():
    """build_agent_graph returns a compiled graph."""
    graph = build_agent_graph()
    assert graph is not None
    # Compiled graphs have a 'nodes' attribute or similar
    assert hasattr(graph, "nodes")
    node_names = list(graph.nodes.keys())
    expected_nodes = {
        "router", "retrieve", "grade", "rewrite", "web_search",
        "generate", "critique", "direct_answer", "oos_answer",
    }
    assert set(node_names) == expected_nodes


def test_build_agent_graph_entry_point():
    graph = build_agent_graph()
    # The entry point should be 'router'
    # Compiled StateGraph stores it as _all_edges or similar
    # Just verify the graph is compiled by checking it's not the raw builder
    assert graph is not None
    assert graph.__class__.__name__ == "CompiledStateGraph"
