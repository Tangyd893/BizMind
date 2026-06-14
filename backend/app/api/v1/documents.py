from app.core.exceptions import AppException
from app.core.pagination import paginate
from app.dependencies import get_current_user, get_db
from app.models import User
from app.schemas.document import DocumentResponse
from app.services.document_service import (
    delete_document,
    get_document,
    list_documents,
    upload_document,
)
from app.services.indexing_service import run_indexing
from fastapi import APIRouter, BackgroundTasks, Depends, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentResponse, status_code=202)
async def upload(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DocumentResponse:
    try:
        doc = await upload_document(session, file, user)
    except ValueError as e:
        raise AppException("VALIDATION_ERROR", str(e), status_code=400) from e

    background_tasks.add_task(run_indexing, str(doc.id))
    return doc


@router.get("")
async def list_docs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: str | None = Query(default=None, alias="status"),
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    items, total = await list_documents(
        session,
        tenant_id=str(user.tenant_id),
        page=page,
        page_size=page_size,
        status_filter=status_filter,
    )
    return paginate(items, total, page, page_size)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_doc(
    document_id: str,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DocumentResponse:
    return await get_document(session, document_id, tenant_id=str(user.tenant_id))


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_doc(
    document_id: str,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    await delete_document(session, document_id, tenant_id=str(user.tenant_id))
