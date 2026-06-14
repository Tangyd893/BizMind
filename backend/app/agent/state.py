"""LangGraph agent state definition."""

from typing import Literal, TypedDict

from langchain_core.messages import BaseMessage


class Citation(TypedDict, total=False):
    document_id: str
    chunk_id: str
    source: str
    page: int | None
    text_preview: str


class ChunkRef(TypedDict, total=False):
    chunk_id: str
    document_id: str
    text: str
    source: str
    page: int | None
    score: float


class AgentState(TypedDict, total=False):
    """Full agent state for the BizMind LangGraph workflow."""
    messages: list[BaseMessage]
    query: str
    rewritten_query: str | None
    retrieved_chunks: list[ChunkRef]
    retrieval_score: float
    retrieval_attempts: int
    generation: str
    critique_passed: bool
    critique_feedback: str | None
    citations: list[Citation]
    route: Literal["direct", "rag", "web", "oos"]
    tenant_id: str
    thread_id: str
    web_search_results: list[dict] | None
    _critique_retries: int
