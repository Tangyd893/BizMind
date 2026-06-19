"""Langfuse observability integration — optional trace/span export.

Enabled when LANGFUSE_ENABLED=true and LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY
are configured. Each agent node execution is recorded as a Langfuse span under
a single trace per chat request.

Usage (in agent_chat_service or graph nodes):
    from app.observability.langfuse_integration import trace_agent_node

    async with trace_agent_node("router", {"query": query}) as span:
        result = await router_node(state)
        span.update(output=result)
"""

from __future__ import annotations

import contextlib
import time
from typing import Any


@contextlib.asynccontextmanager
async def trace_agent_node(node_name: str, input_data: dict | None = None):
    """Context manager that records a Langfuse span for an agent node execution.

    Falls back to a no-op if Langfuse is not configured.
    """
    start = time.perf_counter()
    span = _NoopSpan()
    try:
        # Lazy import — only if Langfuse is configured
        if _is_enabled():
            span = _get_span(node_name, input_data)
        yield span
    except Exception:
        yield span
    finally:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        if isinstance(span, _LangfuseSpan):
            span._finish(elapsed_ms)


class _NoopSpan:
    """No-op span when Langfuse is disabled."""
    async def update(self, **kwargs: Any) -> None:
        pass

    async def end(self) -> None:
        pass


class _LangfuseSpan:
    """Thin wrapper around a Langfuse span."""

    def __init__(self, span: Any) -> None:
        self._span = span
        self._start_ms = int(time.perf_counter() * 1000)

    async def update(self, **kwargs: Any) -> None:
        self._span.update(**kwargs)

    async def end(self) -> None:
        self._span.end()

    def _finish(self, elapsed_ms: int) -> None:
        self._span.update(latency_ms=elapsed_ms)
        self._span.end()


def _is_enabled() -> bool:
    try:
        from app.config import get_settings
        s = get_settings()
        return (
            getattr(s, "langfuse_enabled", False)
            and bool(getattr(s, "langfuse_public_key", ""))
            and bool(getattr(s, "langfuse_secret_key", ""))
        )
    except Exception:
        return False


def _get_span(name: str, input_data: dict | None = None) -> _LangfuseSpan:
    from langfuse import Langfuse

    client = Langfuse(
        public_key=getattr(__import__("app.config").get_settings(), "langfuse_public_key", ""),
        secret_key=getattr(__import__("app.config").get_settings(), "langfuse_secret_key", ""),
        host=getattr(__import__("app.config").get_settings(), "langfuse_host", "http://localhost:3001"),
    )
    trace = client.trace(name=f"agent-{name}")
    span_kwargs = {"name": name}
    if input_data:
        span_kwargs["input"] = input_data
    return _LangfuseSpan(trace.span(**span_kwargs))
