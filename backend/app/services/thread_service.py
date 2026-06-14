"""Thread and message service layer."""

from datetime import UTC

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models import DocumentsVersionCounter, Message, MessageRole, Thread, User
from app.schemas.thread import (
    MessageResponse,
    ThreadMessagesResponse,
    ThreadResponse,
)


async def create_thread(
    session: AsyncSession,
    user: User,
    title: str | None = None,
) -> ThreadResponse:
    """Create a new conversation thread, capturing the current documents version."""
    # Get current version
    result = await session.execute(
        select(DocumentsVersionCounter).where(DocumentsVersionCounter.id == 1)
    )
    counter = result.scalar_one()
    current_version = counter.current_version

    thread = Thread(
        user_id=user.id,
        title=title,
        documents_version=current_version,
    )
    session.add(thread)
    await session.commit()
    await session.refresh(thread)
    return ThreadResponse.model_validate(thread)


async def list_threads(
    session: AsyncSession,
    user_id: str,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[ThreadResponse], int]:
    """List threads for a user, newest first."""
    count_stmt = (
        select(func.count())
        .select_from(Thread)
        .where(Thread.user_id == user_id)
    )
    total = (await session.execute(count_stmt)).scalar() or 0

    stmt = (
        select(Thread)
        .where(Thread.user_id == user_id)
        .order_by(Thread.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = (await session.execute(stmt)).scalars().all()
    items = [ThreadResponse.model_validate(t) for t in rows]
    return items, total


async def get_thread_messages(
    session: AsyncSession,
    thread_id: str,
    user_id: str,
) -> ThreadMessagesResponse:
    """Get all messages for a thread, ensuring the thread belongs to the user."""
    result = await session.execute(
        select(Thread).where(Thread.id == thread_id, Thread.user_id == user_id)
    )
    thread = result.scalar_one_or_none()
    if thread is None:
        raise NotFoundError("Thread not found")

    msg_result = await session.execute(
        select(Message)
        .where(Message.thread_id == thread_id)
        .order_by(Message.created_at.asc())
    )
    messages = msg_result.scalars().all()

    return ThreadMessagesResponse(
        thread_id=str(thread.id),
        is_stale=thread.is_stale,
        documents_version=thread.documents_version,
        messages=[MessageResponse.model_validate(m) for m in messages],
    )


async def save_message(
    session: AsyncSession,
    thread_id: str,
    role: MessageRole,
    content: str,
    citations: list[dict] | None = None,
    token_usage: dict | None = None,
    latency_ms: int | None = None,
) -> Message:
    """Persist a message to the database and update the thread's updated_at."""
    from datetime import datetime

    msg = Message(
        thread_id=thread_id,
        role=role,
        content=content,
        citations=citations or [],
        token_usage=token_usage,
        latency_ms=latency_ms,
    )
    session.add(msg)

    # Touch thread
    result = await session.execute(select(Thread).where(Thread.id == thread_id))
    thread = result.scalar_one()
    thread.updated_at = datetime.now(UTC)

    await session.commit()
    await session.refresh(msg)
    return msg
