"""OpenAI-compatible embedding client.

P1 uses cloud embeddings (text-embedding-3-small by default).
P2 may add local BGE-M3 support.
"""


import httpx

from app.config import get_settings


class EmbeddingClient:
    """Thin wrapper around an OpenAI-compatible embeddings endpoint."""

    def __init__(self) -> None:
        settings = get_settings()
        self._base_url = settings.llm_base_url.rstrip("/")
        self._api_key = settings.llm_api_key
        self._model = settings.embedding_model

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts."""
        if not self._api_key:
            # Return zero vectors for testing when no API key is configured
            return [[0.0] * 1536 for _ in texts]

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self._base_url}/embeddings",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self._model,
                    "input": texts,
                },
            )
            response.raise_for_status()
            data = response.json()
            return [item["embedding"] for item in data["data"]]

    async def embed_single(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        results = await self.embed([text])
        return results[0]


# Singleton
_embedding_client: EmbeddingClient | None = None


def get_embedding_client() -> EmbeddingClient:
    global _embedding_client
    if _embedding_client is None:
        _embedding_client = EmbeddingClient()
    return _embedding_client
