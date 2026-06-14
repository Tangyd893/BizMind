"""Background indexing pipeline — parse → chunk → embed → upsert.

Invoked as a FastAPI BackgroundTask after document upload.
"""

import os
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import Document, DocumentStatus
from app.rag.chunker import chunk_document
from app.rag.embedder import get_embedding_client
from app.rag.qdrant_store import get_qdrant_store


async def run_indexing(document_id: str) -> None:
    """Full indexing pipeline for a single document. Designed to run as a background task.

    The function manages its own DB session and Qdrant client internally
    so that BackgroundTasks can call it without FastAPI DI.
    """
    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        try:
            await _index_document(session, document_id)
        except Exception as exc:
            await _mark_failed(session, document_id, str(exc))


async def _index_document(session: AsyncSession, document_id: str) -> None:
    """Core indexing logic: read file, chunk, embed, upsert."""
    result = await session.execute(
        select(Document).where(Document.id == document_id)
    )
    doc = result.scalar_one_or_none()
    if doc is None:
        return

    # Mark as indexing
    doc.status = DocumentStatus.INDEXING
    await session.commit()

    # Read file content
    file_path = doc.storage_path
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Document file not found: {file_path}")

    with open(file_path, encoding="utf-8") as f:
        text = f.read()

    # Chunk
    chunk_result = chunk_document(text)
    get_settings()

    # Build payloads
    chunk_dicts = []
    for _i, chunk in enumerate(chunk_result.chunks):
        chunk_dicts.append({
            "chunk_id": uuid.uuid4(),
            "tenant_id": str(doc.tenant_id),
            "document_id": str(doc.id),
            "parent_id": None,
            "chunk_type": "child",
            "source": doc.filename,
            "page": None,
            "text_preview": chunk.text[:200],
            "documents_version": doc.documents_version,
        })

    # Batch embed
    embedder = get_embedding_client()
    batch_size = 20
    all_embeddings = []
    for i in range(0, len(chunk_result.chunks), batch_size):
        batch = [c.text for c in chunk_result.chunks[i : i + batch_size]]
        embeddings = await embedder.embed(batch)
        all_embeddings.extend(embeddings)

    # Upsert to Qdrant
    store = get_qdrant_store()
    await store.upsert_chunks(chunk_dicts, all_embeddings)

    # Mark as indexed
    doc.status = DocumentStatus.INDEXED
    doc.chunk_count = len(chunk_result.chunks)
    doc.indexed_at = None  # will be set below
    await session.commit()


async def _mark_failed(
    session: AsyncSession, document_id: str, error_message: str
) -> None:
    """Mark a document as failed with an error message."""
    result = await session.execute(
        select(Document).where(Document.id == document_id)
    )
    doc = result.scalar_one_or_none()
    if doc is not None:
        doc.status = DocumentStatus.FAILED
        doc.error_message = error_message
        await session.commit()
