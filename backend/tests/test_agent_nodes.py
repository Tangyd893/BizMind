"""Agent node unit tests — router, grade, critique with mock LLM."""

from unittest.mock import MagicMock, patch

import pytest

from app.agent.nodes.critique import critique_node
from app.agent.nodes.grade import grade_node
from app.agent.nodes.router import router_node


class _AsyncIter:
    """Wraps a list into an async iterable for mocking LLM streaming."""
    def __init__(self, items: list[str]):
        self._items = items

    def __aiter__(self):
        self._iter = iter(self._items)
        return self

    async def __anext__(self):
        try:
            return next(self._iter)
        except StopIteration:
            raise StopAsyncIteration


@pytest.mark.asyncio
async def test_router_classifies_rag():
    state = {"query": "What is the leave policy?"}
    with patch("app.agent.nodes.router.get_llm_client") as mock_llm:
        mock_llm.return_value.chat_stream.return_value = _AsyncIter(["rag"])
        result = await router_node(state)
    assert result["route"] == "rag"


@pytest.mark.asyncio
async def test_router_classifies_direct():
    state = {"query": "Hello, who are you?"}
    with patch("app.agent.nodes.router.get_llm_client") as mock_llm:
        mock_llm.return_value.chat_stream.return_value = _AsyncIter(["direct"])
        result = await router_node(state)
    assert result["route"] == "direct"


@pytest.mark.asyncio
async def test_router_defaults_to_rag_on_unknown():
    state = {"query": "something weird"}
    with patch("app.agent.nodes.router.get_llm_client") as mock_llm:
        mock_llm.return_value.chat_stream.return_value = _AsyncIter(["xyzzy"])
        result = await router_node(state)
    assert result["route"] == "rag"


@pytest.mark.asyncio
async def test_grade_high_relevance():
    state = {
        "query": "What is the SOP for inventory?",
        "retrieved_chunks": [
            {"source": "erp/inventory-sop.md", "text": "Monthly inventory count procedures..."}
        ],
    }
    with patch("app.agent.nodes.grade.get_llm_client") as mock_llm:
        mock_llm.return_value.chat_stream.return_value = _AsyncIter(
            ['{"score": 0.9, "reason": "Highly relevant"}']
        )
        result = await grade_node(state)
    assert result["retrieval_score"] == 0.9


@pytest.mark.asyncio
async def test_grade_empty_chunks():
    state = {"query": "query", "retrieved_chunks": []}
    result = await grade_node(state)
    assert result["retrieval_score"] == 0.0


@pytest.mark.asyncio
async def test_grade_parse_error_defaults():
    state = {
        "query": "query",
        "retrieved_chunks": [{"source": "doc.md", "text": "some text"}],
    }
    with patch("app.agent.nodes.grade.get_llm_client") as mock_llm:
        mock_llm.return_value.chat_stream.return_value = _AsyncIter(["not valid json"])
        result = await grade_node(state)
    assert result["retrieval_score"] == 0.5


@pytest.mark.asyncio
async def test_critique_passes():
    state = {
        "query": "question",
        "generation": "This is a correct answer.",
        "retrieved_chunks": [{"source": "doc.md", "text": "correct answer information"}],
    }
    with patch("app.agent.nodes.critique.get_llm_client") as mock_llm:
        mock_llm.return_value.chat_stream.return_value = _AsyncIter(
            ['{"passed": true, "feedback": null}']
        )
        result = await critique_node(state)
    assert result["critique_passed"] is True


@pytest.mark.asyncio
async def test_critique_fails():
    state = {
        "query": "question",
        "generation": "This answer has made-up facts.",
        "retrieved_chunks": [{"source": "doc.md", "text": "real facts only"}],
    }
    with patch("app.agent.nodes.critique.get_llm_client") as mock_llm:
        mock_llm.return_value.chat_stream.return_value = _AsyncIter(
            ['{"passed": false, "feedback": "Contains hallucination"}']
        )
        result = await critique_node(state)
    assert result["critique_passed"] is False
    assert result["critique_feedback"] is not None
