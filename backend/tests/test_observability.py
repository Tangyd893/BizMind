"""Tests for optional Langfuse integration (no-op when disabled)."""

import pytest

from app.observability.langfuse_integration import (
    _NoopSpan,
    _is_enabled,
    trace_agent_node,
)


@pytest.mark.asyncio
async def test_trace_agent_node_noop_when_disabled():
    async with trace_agent_node("router", {"query": "hi"}) as span:
        assert isinstance(span, _NoopSpan)
        await span.update(output={"route": "rag"})


def test_is_enabled_false_without_config(monkeypatch):
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "langfuse_enabled", False)
    monkeypatch.setattr(get_settings(), "langfuse_public_key", "")
    monkeypatch.setattr(get_settings(), "langfuse_secret_key", "")
    assert _is_enabled() is False


@pytest.mark.asyncio
async def test_noop_span_accepts_update_and_end():
    span = _NoopSpan()
    await span.update(foo="bar")
    await span.end()
