import uuid
from datetime import UTC, datetime, timedelta
from uuid import UUID

import bcrypt
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.exceptions import ConflictError, UnauthorizedError
from app.models import Tenant, User
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UserResponse


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def _create_token(user: User) -> tuple[str, int]:
    settings = get_settings()
    now = datetime.now(UTC)
    expire = now + timedelta(hours=settings.jwt_expire_hours)
    expires_in = int(expire.timestamp())

    payload = {
        "sub": str(user.id),
        "tenant_id": str(user.tenant_id),
        "role": user.role.value,
        "exp": expires_in,
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)
    return token, settings.jwt_expire_hours * 3600


def _user_to_response(user: User) -> UserResponse:
    return UserResponse(
        id=str(user.id),
        email=user.email,
        role=user.role.value,
        tenant_id=str(user.tenant_id),
        created_at=user.created_at,
    )


async def register(session: AsyncSession, req: RegisterRequest) -> AuthResponse:
    existing = await session.execute(select(User).where(User.email == req.email))
    if existing.scalar_one_or_none() is not None:
        raise ConflictError("Email already registered")

    tenant = Tenant(name=req.tenant_name or "Personal Workspace")
    session.add(tenant)
    await session.flush()

    user = User(
        tenant_id=tenant.id,
        email=req.email,
        password_hash=_hash_password(req.password),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    token, expires_in = _create_token(user)
    return AuthResponse(user=_user_to_response(user), access_token=token, expires_in=expires_in)


async def login(session: AsyncSession, req: LoginRequest) -> AuthResponse:
    result = await session.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()

    if user is None or not _verify_password(req.password, user.password_hash):
        raise UnauthorizedError("Invalid email or password")

    token, expires_in = _create_token(user)
    return AuthResponse(user=_user_to_response(user), access_token=token, expires_in=expires_in)


async def get_current_user(
    session: AsyncSession, token: str
) -> User:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise UnauthorizedError("Invalid or expired token") from exc

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise UnauthorizedError("Invalid token payload")

    result = await session.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise UnauthorizedError("User not found")

    return user
