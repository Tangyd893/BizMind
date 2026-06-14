import hashlib
import os
from datetime import UTC, datetime

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import Document, User
from app.schemas.document import DocumentResponse

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "text/markdown",
    "text/plain",
}


def _validate_mime(filename: str, mime_type: str) -> None:
    """Raise ValueError if file type is not allowed."""
    if mime_type not in ALLOWED_MIME_TYPES:
        # Also check by extension for markdown files that browsers misreport
        ext = os.path.splitext(filename)[1].lower()
        if ext == ".md" and mime_type in ("text/plain", "application/octet-stream"):
            return  # accept .md files even with generic mime
        raise ValueError(
            f"Unsupported file type: {mime_type}. "
            f"Allowed: {', '.join(sorted(ALLOWED_MIME_TYPES))}"
        )


def _compute_sha256(file_path: str) -> str:
    """Compute SHA-256 hash of a file on disk."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


async def upload_document(
    session: AsyncSession,
    file: UploadFile,
    user: User,
) -> DocumentResponse:
    settings = get_settings()

    if not file.filename:
        raise ValueError("Filename is required")

    mime_type = file.content_type or "application/octet-stream"
    _validate_mime(file.filename, mime_type)

    # Read content and check size
    content = await file.read()
    if len(content) > settings.max_upload_size_mb * 1024 * 1024:
        raise ValueError(
            f"File exceeds maximum size of {settings.max_upload_size_mb} MB"
        )

    # Save to disk
    os.makedirs(settings.storage_path, exist_ok=True)
    safe_name = f"{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}_{file.filename}"
    file_path = os.path.join(settings.storage_path, safe_name)
    with open(file_path, "wb") as f:
        f.write(content)

    content_hash = _compute_sha256(file_path)

    doc = Document(
        tenant_id=user.tenant_id,
        owner_id=user.id,
        filename=file.filename,
        mime_type=mime_type,
        storage_path=file_path,
        content_hash=content_hash,
    )
    session.add(doc)
    await session.commit()
    await session.refresh(doc)

    return DocumentResponse.model_validate(doc)


async def list_documents(
    session: AsyncSession,
    tenant_id: str,
    page: int = 1,
    page_size: int = 20,
    status_filter: str | None = None,
) -> tuple[list[DocumentResponse], int]:
    """List documents for a tenant with optional status filter."""
    from sqlalchemy import func, select

    stmt = select(Document).where(Document.tenant_id == tenant_id)
    if status_filter:
        stmt = stmt.where(Document.status == status_filter)
    stmt = stmt.order_by(Document.created_at.desc())

    # Count
    count_stmt = select(func.count()).select_from(Document).where(
        Document.tenant_id == tenant_id
    )
    if status_filter:
        count_stmt = count_stmt.where(Document.status == status_filter)
    total = (await session.execute(count_stmt)).scalar() or 0

    # Paginate
    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)
    rows = (await session.execute(stmt)).scalars().all()

    items = [DocumentResponse.model_validate(d) for d in rows]
    return items, total


async def get_document(
    session: AsyncSession,
    document_id: str,
    tenant_id: str,
) -> DocumentResponse:
    """Get a single document, scoped to tenant."""
    from sqlalchemy import select

    result = await session.execute(
        select(Document).where(
            Document.id == document_id,
            Document.tenant_id == tenant_id,
        )
    )
    doc = result.scalar_one_or_none()
    if doc is None:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Document not found")
    return DocumentResponse.model_validate(doc)


async def delete_document(
    session: AsyncSession,
    document_id: str,
    tenant_id: str,
) -> None:
    """Delete a document, its file, Qdrant vectors, and bump version."""
    import os as _os

    from sqlalchemy import select

    result = await session.execute(
        select(Document).where(
            Document.id == document_id,
            Document.tenant_id == tenant_id,
        )
    )
    doc = result.scalar_one_or_none()
    if doc is None:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Document not found")

    # Delete Qdrant vectors
    from app.rag.qdrant_store import get_qdrant_store
    store = get_qdrant_store()
    await store.delete_by_document(tenant_id, str(doc.id))

    # Delete file from disk
    if _os.path.exists(doc.storage_path):
        _os.remove(doc.storage_path)

    # Bump version
    await _bump_version(session)

    # Delete DB record
    await session.delete(doc)
    await session.commit()


async def _bump_version(session: AsyncSession) -> None:
    """Increment the global documents_version counter and mark stale threads."""
    from sqlalchemy import select, update

    from app.models import DocumentsVersionCounter, Thread

    result = await session.execute(
        select(DocumentsVersionCounter).where(DocumentsVersionCounter.id == 1)
    )
    counter = result.scalar_one()
    counter.current_version += 1

    # Mark all threads as stale
    await session.execute(
        update(Thread).values(is_stale=True)
    )

