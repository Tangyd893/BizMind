"""Qdrant vector store — upsert, delete, search operations."""


from qdrant_client import AsyncQdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse

from app.config import get_settings


class QdrantStore:
    """Async wrapper around Qdrant for chunk storage and retrieval."""

    def __init__(self) -> None:
        settings = get_settings()
        self._client = AsyncQdrantClient(url=settings.qdrant_url)
        self._collection = settings.qdrant_collection
        self._vector_size = 1536  # text-embedding-3-small dimension

    async def ensure_collection(self) -> None:
        """Create the collection if it doesn't already exist."""
        try:
            await self._client.get_collection(self._collection)
        except UnexpectedResponse:
            await self._client.create_collection(
                collection_name=self._collection,
                vectors_config=models.VectorParams(
                    size=self._vector_size,
                    distance=models.Distance.COSINE,
                ),
            )

    async def upsert_chunks(
        self,
        chunks: list[dict],
        embeddings: list[list[float]],
    ) -> None:
        """Insert or update chunk vectors with metadata payloads.

        Each chunk dict should contain: chunk_id, tenant_id, document_id,
        parent_id, chunk_type, source, page, text_preview, documents_version.
        """
        if not chunks:
            return

        await self.ensure_collection()

        points = [
            models.PointStruct(
                id=str(c["chunk_id"]),
                vector=emb,
                payload={
                    "tenant_id": c["tenant_id"],
                    "document_id": c["document_id"],
                    "parent_id": c.get("parent_id"),
                    "chunk_type": c.get("chunk_type", "child"),
                    "source": c.get("source", ""),
                    "page": c.get("page"),
                    "text_preview": c.get("text_preview", ""),
                    "documents_version": c.get("documents_version", 0),
                },
            )
            for c, emb in zip(chunks, embeddings, strict=False)
        ]

        await self._client.upsert(
            collection_name=self._collection,
            points=points,
        )

    async def delete_by_document(self, tenant_id: str, document_id: str) -> None:
        """Delete all chunks belonging to a document."""
        await self._client.delete(
            collection_name=self._collection,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="tenant_id",
                            match=models.MatchValue(value=tenant_id),
                        ),
                        models.FieldCondition(
                            key="document_id",
                            match=models.MatchValue(value=document_id),
                        ),
                    ]
                )
            ),
        )

    async def search(
        self,
        query_vector: list[float],
        tenant_id: str,
        top_k: int = 20,
    ) -> list[dict]:
        """Search for the most similar chunks, filtered by tenant."""
        await self.ensure_collection()

        results = await self._client.search(
            collection_name=self._collection,
            query_vector=query_vector,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="tenant_id",
                        match=models.MatchValue(value=tenant_id),
                    ),
                ]
            ),
            limit=top_k,
            with_payload=True,
        )

        return [
            {
                "chunk_id": r.id,
                "score": r.score,
                **r.payload,
            }
            for r in results
        ]


# Singleton
_qdrant_store: QdrantStore | None = None


def get_qdrant_store() -> QdrantStore:
    global _qdrant_store
    if _qdrant_store is None:
        _qdrant_store = QdrantStore()
    return _qdrant_store
