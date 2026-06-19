"""Tests for rag/llm_client.py and rag/embedder.py — mock httpx, test fallbacks."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ═══════════════════════════════════════════════════════════════════════
# LLMClient tests
# ═══════════════════════════════════════════════════════════════════════

class TestLLMClient:
    """Tests for LLMClient.chat_stream."""

    @pytest.mark.asyncio
    async def test_returns_mock_when_no_api_key(self):
        """When api_key is empty, yield mock message."""
        from app.rag.llm_client import LLMClient

        client = LLMClient()
        client._api_key = ""  # simulate no key

        tokens = []
        async for token in client.chat_stream([{"role": "user", "content": "hi"}]):
            tokens.append(token)

        assert len(tokens) == 1
        assert "mock response" in tokens[0]

    @pytest.mark.asyncio
    async def test_streams_sse_tokens(self):
        """With API key, parse SSE stream from httpx."""
        from app.rag.llm_client import LLMClient

        # Build mock SSE response lines
        sse_lines = [
            'data: {"choices":[{"delta":{"content":"Hello"}}]}\n',
            'data: {"choices":[{"delta":{"content":" World"}}]}\n',
            'data: [DONE]\n',
        ]

        mock_stream = MagicMock()
        mock_stream.aiter_lines.return_value = _aiter(sse_lines)
        mock_stream.__aenter__.return_value = mock_stream
        mock_stream.__aexit__.return_value = None

        mock_client = MagicMock()
        mock_client.stream.return_value = mock_stream
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        client = LLMClient()
        client._api_key = "sk-test"

        with patch("httpx.AsyncClient", return_value=mock_client):
            tokens = []
            async for token in client.chat_stream(
                [{"role": "user", "content": "hi"}],
                temperature=0.3,
                max_tokens=100,
            ):
                tokens.append(token)

        assert tokens == ["Hello", " World"]

    @pytest.mark.asyncio
    async def test_skips_json_decode_errors(self):
        """Malformed JSON in SSE stream is silently skipped."""
        from app.rag.llm_client import LLMClient

        sse_lines = [
            'data: {invalid json}\n',
            'data: {"choices":[{"delta":{"content":"valid"}}]}\n',
            'data: [DONE]\n',
        ]

        mock_stream = MagicMock()
        mock_stream.aiter_lines.return_value = _aiter(sse_lines)
        mock_stream.__aenter__.return_value = mock_stream
        mock_stream.__aexit__.return_value = None

        mock_client = MagicMock()
        mock_client.stream.return_value = mock_stream
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        client = LLMClient()
        client._api_key = "sk-test"

        with patch("httpx.AsyncClient", return_value=mock_client):
            tokens = []
            async for token in client.chat_stream([{"role": "user", "content": "x"}]):
                tokens.append(token)

        assert tokens == ["valid"]

    @pytest.mark.asyncio
    async def test_stops_on_done_signal(self):
        """SSE [DONE] stops iteration immediately."""
        from app.rag.llm_client import LLMClient

        sse_lines = [
            'data: {"choices":[{"delta":{"content":"first"}}]}\n',
            'data: [DONE]\n',
            'data: {"choices":[{"delta":{"content":"should-not-appear"}}]}\n',
        ]

        mock_stream = MagicMock()
        mock_stream.aiter_lines.return_value = _aiter(sse_lines)
        mock_stream.__aenter__.return_value = mock_stream
        mock_stream.__aexit__.return_value = None

        mock_client = MagicMock()
        mock_client.stream.return_value = mock_stream
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        client = LLMClient()
        client._api_key = "sk-test"

        with patch("httpx.AsyncClient", return_value=mock_client):
            tokens = []
            async for token in client.chat_stream([{"role": "user", "content": "x"}]):
                tokens.append(token)

        assert tokens == ["first"]

    def test_get_llm_client_singleton(self):
        """get_llm_client returns same instance."""
        from app.rag.llm_client import get_llm_client, _llm_client

        # Reset singleton for test
        import app.rag.llm_client as mod
        mod._llm_client = None

        c1 = get_llm_client()
        c2 = get_llm_client()
        assert c1 is c2


# ═══════════════════════════════════════════════════════════════════════
# EmbeddingClient tests
# ═══════════════════════════════════════════════════════════════════════

class TestEmbeddingClient:
    """Tests for EmbeddingClient.embed and embed_single."""

    @pytest.mark.asyncio
    async def test_returns_zero_vectors_when_no_api_key(self):
        """When api_key is empty, return 1536-dim zero vectors."""
        from app.rag.embedder import EmbeddingClient

        client = EmbeddingClient()
        client._api_key = ""

        vectors = await client.embed(["hello", "world"])
        assert len(vectors) == 2
        assert len(vectors[0]) == 1536
        assert all(v == 0.0 for v in vectors[0])

    @pytest.mark.asyncio
    async def test_embed_calls_api_with_correct_payload(self):
        """With API key, calls the embeddings endpoint with correct body."""
        from app.rag.embedder import EmbeddingClient

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {"embedding": [0.1, 0.2, 0.3]},
                {"embedding": [0.4, 0.5, 0.6]},
            ]
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        client = EmbeddingClient()
        client._api_key = "sk-test"
        client._base_url = "https://api.test.com/v1"
        client._model = "test-model"

        with patch("httpx.AsyncClient", return_value=mock_client):
            vectors = await client.embed(["text1", "text2"])

        assert vectors == [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        # Verify the API call
        call_args = mock_client.post.call_args
        assert "https://api.test.com/v1/embeddings" in str(call_args)
        json_body = call_args.kwargs["json"]
        assert json_body["model"] == "test-model"
        assert json_body["input"] == ["text1", "text2"]

    @pytest.mark.asyncio
    async def test_embed_single_delegates_to_embed(self):
        """embed_single calls embed and returns first result."""
        from app.rag.embedder import EmbeddingClient

        client = EmbeddingClient()
        client._api_key = ""

        vector = await client.embed_single("test")
        assert len(vector) == 1536
        assert all(v == 0.0 for v in vector)

    @pytest.mark.asyncio
    async def test_embed_raises_on_http_error(self):
        """HTTP error propagates via raise_for_status."""
        from app.rag.embedder import EmbeddingClient

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("HTTP 500")

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        client = EmbeddingClient()
        client._api_key = "sk-test"

        with patch("httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(Exception, match="HTTP 500"):
                await client.embed(["text"])


# ═══════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════

class _aiter:
    """Convert a list into an async iterable."""
    def __init__(self, items):
        self._items = items

    def __aiter__(self):
        self._iter = iter(self._items)
        return self

    async def __anext__(self):
        try:
            return next(self._iter)
        except StopIteration:
            raise StopAsyncIteration


# ═══════════════════════════════════════════════════════════════════════
# CachedEmbeddingClient tests
# ═══════════════════════════════════════════════════════════════════════

class TestCachedEmbeddingClient:
    """Tests for CachedEmbeddingClient cache key and fallback."""

    def test_cache_key_deterministic(self):
        """Same text produces same key."""
        from app.rag.embedding_cache import CachedEmbeddingClient
        k1 = CachedEmbeddingClient._cache_key("hello")
        k2 = CachedEmbeddingClient._cache_key("hello")
        assert k1 == k2
        assert k1.startswith("emb:")
        assert len(k1) == 68  # "emb:" + 64 hex chars

    def test_cache_key_different_texts(self):
        """Different texts produce different keys."""
        from app.rag.embedding_cache import CachedEmbeddingClient
        assert CachedEmbeddingClient._cache_key("a") != CachedEmbeddingClient._cache_key("b")

    @pytest.mark.asyncio
    async def test_falls_back_when_redis_unavailable(self):
        """When Redis is down, falls back to direct embed call."""
        from app.rag.embedding_cache import CachedEmbeddingClient

        client = CachedEmbeddingClient()
        client._inner._api_key = ""  # no API key → zero vectors for inner too

        with patch.object(client, "_get_redis", side_effect=RuntimeError("Redis down")):
            vectors = await client.embed(["text1", "text2"])
        assert len(vectors) == 2
        assert len(vectors[0]) == 1536
