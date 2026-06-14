"""Redis embedding cache — SHA256-based cache for embedding vectors.

Caches embedding results in Redis with a configurable TTL (default 7 days).
Significantly reduces API costs for repeated queries and document chunks.
"""

import hashlib

from app.config import get_settings
from app.rag.embedder import EmbeddingClient


class CachedEmbeddingClient:
    """Wraps EmbeddingClient with Redis caching."""

    def __init__(self) -> None:
        self._inner = EmbeddingClient()
        self._ttl = 7 * 24 * 3600  # 7 days

    @staticmethod
    def _cache_key(text: str) -> str:
        """Generate a deterministic key for a text string."""
        h = hashlib.sha256(text.encode("utf-8")).hexdigest()
        return f"emb:{h}"

    async def _get_redis(self):
        """Lazy Redis connection."""
        import redis.asyncio as aioredis
        settings = get_settings()
        return aioredis.from_url(settings.redis_url)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings with Redis caching."""
        keys = [self._cache_key(t) for t in texts]
        results: dict[str, list[float] | None] = {}

        try:
            r = await self._get_redis()
            pipeline = r.pipeline()
            for key in keys:
                pipeline.get(key)
            cached = await pipeline.execute()

            # Collect cache hits
            uncached_texts = []
            uncached_indices = []
            for i, (text, _key, val) in enumerate(zip(texts, keys, cached, strict=False)):
                if val is not None:
                    import json
                    results[text] = json.loads(val)
                else:
                    uncached_texts.append(text)
                    uncached_indices.append(i)

            # Generate embeddings for cache misses
            if uncached_texts:
                new_embs = await self._inner.embed(uncached_texts)
                pipeline2 = r.pipeline()
                for text, emb in zip(uncached_texts, new_embs, strict=True):
                    import json
                    key = self._cache_key(text)
                    results[text] = emb
                    pipeline2.setex(key, self._ttl, json.dumps(emb))
                await pipeline2.execute()

            await r.aclose()
        except Exception:
            # Redis unavailable — fall back to direct API calls
            return await self._inner.embed(texts)

        return [results[t] for t in texts]  # type: ignore[misc]

    async def embed_single(self, text: str) -> list[float]:
        """Generate embedding for a single text, with caching."""
        results = await self.embed([text])
        return results[0]


# Singleton
_cached_client: CachedEmbeddingClient | None = None


def get_cached_embedding_client() -> CachedEmbeddingClient:
    global _cached_client
    if _cached_client is None:
        _cached_client = CachedEmbeddingClient()
    return _cached_client
