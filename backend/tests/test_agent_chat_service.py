"""Tests for agent_chat_service — SSE formatting and streaming orchestration."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.agent_chat_service import _sse_event, stream_agent_chat


def test_sse_event_basic():
    result = _sse_event("token", {"content": "Hello"})
    assert result.startswith("event: token\n")
    assert "data: " in result
    assert result.endswith("\n\n")
    data_str = result.split("data: ")[1].rstrip("\n")
    data = json.loads(data_str)
    assert data["content"] == "Hello"


def test_sse_event_with_complex_data():
    result = _sse_event("citation", {
        "source": "doc.md",
        "text": "Some referenced text",
        "score": 0.95,
    })
    assert result.startswith("event: citation\n")
    data_str = result.split("data: ")[1].rstrip("\n")
    data = json.loads(data_str)
    assert data["source"] == "doc.md"
    assert data["score"] == 0.95


def test_sse_event_done():
    result = _sse_event("done", {
        "message_id": "abc-123",
        "route": "rag",
        "total_latency_ms": 1500,
    })
    assert "event: done" in result
    data_str = result.split("data: ")[1].rstrip("\n")
    data = json.loads(data_str)
    assert data["message_id"] == "abc-123"
    assert data["total_latency_ms"] == 1500


def test_sse_event_error():
    result = _sse_event("error", {
        "code": "INTERNAL_ERROR",
        "message": "Something went wrong",
    })
    assert "event: error" in result
    data_str = result.split("data: ")[1].rstrip("\n")
    data = json.loads(data_str)
    assert data["code"] == "INTERNAL_ERROR"


def test_sse_event_serializes_non_json_types():
    """default=str converts non-serializable types like UUID."""
    from uuid import UUID

    uid = UUID("12345678-1234-5678-1234-567812345678")
    result = _sse_event("done", {"message_id": uid})
    data_str = result.split("data: ")[1].rstrip("\n")
    data = json.loads(data_str)
    assert data["message_id"] == str(uid)


# ── stream_agent_chat integration tests ──────────────────────────────

class _AsyncIter:
    """Wraps a list into an async iterable for mocking graph.astream."""
    def __init__(self, items: list):
        self._items = items

    def __aiter__(self):
        self._iter = iter(self._items)
        return self

    async def __anext__(self):
        try:
            return next(self._iter)
        except StopIteration:
            raise StopAsyncIteration


@pytest.fixture
def mock_user():
    """Minimal User object for testing."""
    user = MagicMock()
    user.tenant_id = "550e8400-e29b-41d4-a716-446655440000"
    user.id = "660e8400-e29b-41d4-a716-446655440001"
    return user


@pytest.fixture
def mock_saved_message():
    """Mock Message returned by save_message."""
    from uuid import UUID
    msg = MagicMock()
    msg.id = UUID("770e8400-e29b-41d4-a716-446655440002")
    return msg


@pytest.mark.asyncio
async def test_stream_agent_chat_yields_agent_steps_and_tokens(mock_user, mock_saved_message):
    """Full SSE stream: agent_step → token → done events."""
    mock_session = AsyncMock()
    mock_session_factory = AsyncMock()
    mock_session_factory.__aenter__.return_value = mock_session

    mock_graph = MagicMock()
    mock_graph.astream.return_value = _AsyncIter([
        {"router": {"route": "rag"}},
        {"retrieve": {"retrieved_chunks": [{"source": "doc.md", "text_preview": "content"}]}},
        {"grade": {"retrieval_score": 0.9}},
        {"generate": {
            "generation": "This is the answer",
            "citations": [{"source": "doc.md", "text_preview": "content..."}],
        }},
        {"critique": {"critique_passed": True}},
    ])

    with (
        patch("app.db.session.AsyncSessionLocal", return_value=mock_session_factory),
        patch("app.services.agent_chat_service.save_message", return_value=mock_saved_message),
        patch("app.services.agent_chat_service.build_agent_graph", return_value=mock_graph),
    ):
        events = []
        async for event_str in stream_agent_chat(mock_user, "thread-1", "test query"):
            events.append(event_str)

    # Should have agent_step + token + citation + done events
    event_types = []
    for e in events:
        for line in e.split("\n"):
            if line.startswith("event: "):
                event_types.append(line[7:])

    assert "agent_step" in event_types
    assert "token" in event_types
    assert "done" in event_types
    # Token content should be spaced words
    token_events = [e for e in events if e.startswith("event: token")]
    assert len(token_events) > 0


@pytest.mark.asyncio
async def test_stream_agent_chat_yields_error_on_exception(mock_user):
    """Exception during graph execution → error event."""
    mock_session = AsyncMock()
    mock_session_factory = AsyncMock()
    mock_session_factory.__aenter__.return_value = mock_session

    with (
        patch("app.db.session.AsyncSessionLocal", return_value=mock_session_factory),
        patch("app.services.agent_chat_service.save_message", side_effect=RuntimeError("DB down")),
    ):
        events = []
        async for event_str in stream_agent_chat(mock_user, "thread-1", "query"):
            events.append(event_str)

    error_events = [e for e in events if e.startswith("event: error")]
    assert len(error_events) == 1
    error_data = json.loads(error_events[0].split("data: ")[1].rstrip("\n"))
    assert error_data["code"] == "INTERNAL_ERROR"
    assert "DB down" in error_data["message"]


@pytest.mark.asyncio
async def test_stream_agent_chat_done_has_metadata(mock_user, mock_saved_message):
    """Done event carries message_id, route, latency."""
    mock_session = AsyncMock()
    mock_session_factory = AsyncMock()
    mock_session_factory.__aenter__.return_value = mock_session

    mock_graph = MagicMock()
    mock_graph.astream.return_value = _AsyncIter([
        {"router": {"route": "rag"}},
        {"generate": {"generation": "Answer", "citations": []}},
    ])

    with (
        patch("app.db.session.AsyncSessionLocal", return_value=mock_session_factory),
        patch("app.services.agent_chat_service.save_message", return_value=mock_saved_message),
        patch("app.services.agent_chat_service.build_agent_graph", return_value=mock_graph),
    ):
        events = []
        async for event_str in stream_agent_chat(mock_user, "thread-1", "query"):
            events.append(event_str)

    done_events = [e for e in events if e.startswith("event: done")]
    assert len(done_events) == 1
    done_data = json.loads(done_events[0].split("data: ")[1].rstrip("\n"))
    assert done_data["message_id"] == str(mock_saved_message.id)
    assert done_data["route"] == "rag"
    assert "total_latency_ms" in done_data


@pytest.mark.asyncio
async def test_stream_agent_chat_saves_user_message_first(mock_user, mock_saved_message):
    """User message saved before graph execution."""
    mock_session = AsyncMock()
    mock_session_factory = AsyncMock()
    mock_session_factory.__aenter__.return_value = mock_session

    mock_graph = MagicMock()
    mock_graph.astream.return_value = _AsyncIter([])

    with (
        patch("app.db.session.AsyncSessionLocal", return_value=mock_session_factory),
        patch("app.services.agent_chat_service.save_message") as mock_save,
        patch("app.services.agent_chat_service.build_agent_graph", return_value=mock_graph),
    ):
        mock_save.return_value = mock_saved_message
        events = []
        async for event_str in stream_agent_chat(mock_user, "thread-1", "hello world"):
            events.append(event_str)

    from app.models import MessageRole

    # First call should save USER message
    assert mock_save.call_count >= 2
    first_call_args = mock_save.call_args_list[0][0]
    assert first_call_args[2] == MessageRole.USER
    assert first_call_args[3] == "hello world"
