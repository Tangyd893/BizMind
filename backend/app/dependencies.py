from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedError
from app.core.rbac import require_admin
from app.db.session import get_db_session
from app.models import User


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db_session():
        yield session


async def get_current_user(
    authorization: str | None = Header(None, description="Bearer <token>"),
    session: AsyncSession = Depends(get_db),
):
    """Extract and validate the current user from the Bearer token."""
    from app.services.auth_service import get_current_user as _resolve_user

    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedError("Missing or invalid Authorization header")

    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise UnauthorizedError("Empty token")

    return await _resolve_user(session, token)


async def get_current_admin(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Require admin role — raises 403 if the user is not an admin."""
    require_admin(user)
    return user
