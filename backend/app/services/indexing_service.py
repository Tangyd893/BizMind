"""Background indexing pipeline — parse → chunk → embed → upsert.

Invoked as a FastAPI BackgroundTask after document upload.
"""

import os
import uuid


def _extract_pdf_text(file_path: str) -> str:
    """Extract text from a PDF file using PyMuPDF (fitz)."""
    import fitz  # PyMuPDF

    text_parts: list[str] = []
    doc = fitz.open(file_path)
    try:
        for page in doc:
            text = page.get_text()
            if text.strip():
                text_parts.append(text.strip())
    finally:
        doc.close()

    if not text_parts:
        raise ValueError(f"PDF contains no extractable text: {file_path}")
    return "\n\n".join(text_parts)

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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

    # Extract text based on mime type
    if doc.mime_type == "application/pdf":
        text = _extract_pdf_text(file_path)
    else:
        with open(file_path, encoding="utf-8") as f:
            text = f.read()

    # Chunk (parent-child per ADR-003)
    chunk_result = chunk_document(text)

    # Build parent ID map: index → UUID
    parent_ids: dict[int, uuid.UUID] = {}
    for p in chunk_result.parent_chunks:
        parent_ids[p.index] = uuid.uuid4()

    # Build child payloads with parent linking
    child_dicts = []
    for _i, chunk in enumerate(chunk_result.chunks):
        pid = parent_ids.get(chunk.parent_index) if chunk.parent_index is not None else None
        child_dicts.append({
            "chunk_id": uuid.uuid4(),
            "tenant_id": str(doc.tenant_id),
            "document_id": str(doc.id),
            "parent_id": str(pid) if pid else None,
            "chunk_type": "child",
            "source": doc.filename,
            "page": None,
            "text_preview": chunk.text[:200],
            "documents_version": doc.documents_version,
        })

    # Also build parent payloads (stored alongside for retrieval context)
    parent_dicts = []
    for p in chunk_result.parent_chunks:
        pid = parent_ids[p.index]
        parent_dicts.append({
            "chunk_id": pid,
            "tenant_id": str(doc.tenant_id),
            "document_id": str(doc.id),
            "parent_id": None,
            "chunk_type": "parent",
            "source": doc.filename,
            "page": None,
            "text_preview": p.text[:200],
            "documents_version": doc.documents_version,
        })

    all_dicts = child_dicts + parent_dicts
    all_texts = [c.text for c in chunk_result.chunks] + [p.text for p in chunk_result.parent_chunks]

    # Batch embed all (children + parents)
    embedder = get_embedding_client()
    batch_size = 20
    all_embeddings = []
    for i in range(0, len(all_texts), batch_size):
        batch_texts = all_texts[i : i + batch_size]
        embeddings = await embedder.embed(batch_texts)
        all_embeddings.extend(embeddings)

    # Upsert to Qdrant
    store = get_qdrant_store()
    await store.upsert_chunks(all_dicts, all_embeddings)

    # Mark as indexed
    doc.status = DocumentStatus.INDEXED
    doc.chunk_count = len(chunk_result.chunks)
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
