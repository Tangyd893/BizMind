from app.core.pagination import paginate
from app.dependencies import get_current_user, get_db
from app.models import User
from app.schemas.thread import CreateThreadRequest, ThreadMessagesResponse, ThreadResponse
from app.services.thread_service import (
    create_thread,
    get_thread_messages,
    list_threads,
)
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

router = APIRouter(prefix="/threads", tags=["threads"])


@router.post("", response_model=ThreadResponse, status_code=status.HTTP_201_CREATED)
async def create(
    req: CreateThreadRequest,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ThreadResponse:
    return await create_thread(session, user, title=req.title)


@router.get("")
async def list_all(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    items, total = await list_threads(
        session,
        user_id=str(user.id),
        page=page,
        page_size=page_size,
    )
    return paginate(items, total, page, page_size)


@router.get("/{thread_id}/messages", response_model=ThreadMessagesResponse)
async def get_messages(
    thread_id: str,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ThreadMessagesResponse:
    return await get_thread_messages(session, thread_id, user_id=str(user.id))
