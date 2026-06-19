"""Tests for rag/retriever.py — retrieve and hybrid_retrieve with mocked dependencies."""

from unittest.mock import AsyncMock, patch

import pytest

from app.rag.retriever import RetrievedChunk, RetrievalResult, retrieve


def _make_search_result(chunk_id="c1", doc_id="d1", source="test.md",
                        text="sample text", score=0.85, page=None):
    return {
        "chunk_id": chunk_id,
        "document_id": doc_id,
        "source": source,
        "text_preview": text,
        "score": score,
        "page": page,
    }


class TestRetrieve:
    """Tests for the single-stage dense retrieval."""

    @pytest.mark.asyncio
    async def test_retrieve_returns_chunks(self):
        fake_embedder = AsyncMock()
        fake_embedder.embed_single.return_value = [0.1] * 1536

        fake_store = AsyncMock()
        fake_store.search.return_value = [
            _make_search_result("c1", "d1", "a.md", "text a", 0.9),
            _make_search_result("c2", "d2", "b.md", "text b", 0.7),
        ]

        with (
            patch("app.rag.retriever.get_embedding_client", return_value=fake_embedder),
            patch("app.rag.retriever.get_qdrant_store", return_value=fake_store),
        ):
            result = await retrieve("test query", "tenant-1", top_k=3)

        assert isinstance(result, RetrievalResult)
        assert len(result.chunks) == 2
        assert result.chunks[0].chunk_id == "c1"
        assert result.chunks[0].score == 0.9
        assert result.chunks[1].source == "b.md"
        assert result.latency_ms >= 0

    @pytest.mark.asyncio
    async def test_retrieve_uses_default_top_k(self):
        fake_embedder = AsyncMock()
        fake_embedder.embed_single.return_value = [0.0] * 1536
        fake_store = AsyncMock()
        fake_store.search.return_value = []

        with (
            patch("app.rag.retriever.get_embedding_client", return_value=fake_embedder),
            patch("app.rag.retriever.get_qdrant_store", return_value=fake_store),
        ):
            await retrieve("query", "tenant-1")

        # Should have used default retrieval_top_k from settings
        call_kwargs = fake_store.search.call_args.kwargs
        from app.config import get_settings
        assert call_kwargs["top_k"] == get_settings().retrieval_top_k

    @pytest.mark.asyncio
    async def test_retrieve_passes_tenant_id(self):
        fake_embedder = AsyncMock()
        fake_embedder.embed_single.return_value = [0.0] * 1536
        fake_store = AsyncMock()
        fake_store.search.return_value = []

        with (
            patch("app.rag.retriever.get_embedding_client", return_value=fake_embedder),
            patch("app.rag.retriever.get_qdrant_store", return_value=fake_store),
        ):
            await retrieve("query", "tenant-42")

        call_kwargs = fake_store.search.call_args.kwargs
        assert call_kwargs["tenant_id"] == "tenant-42"

    @pytest.mark.asyncio
    async def test_retrieve_handles_page_field(self):
        fake_embedder = AsyncMock()
        fake_embedder.embed_single.return_value = [0.0] * 1536
        fake_store = AsyncMock()
        fake_store.search.return_value = [
            _make_search_result("c1", "d1", "doc.pdf", "pdf text", 0.8, page=3),
            _make_search_result("c2", "d2", "doc2.pdf", "more text", 0.6, page=None),
        ]

        with (
            patch("app.rag.retriever.get_embedding_client", return_value=fake_embedder),
            patch("app.rag.retriever.get_qdrant_store", return_value=fake_store),
        ):
            result = await retrieve("query", "tenant-1", top_k=5)

        assert result.chunks[0].page == 3
        assert result.chunks[1].page is None
