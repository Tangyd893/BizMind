"""Admin routes — tenant-scoped user management (admin only)."""

from app.core.pagination import paginate
from app.dependencies import get_current_admin, get_db
from app.models import User
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users")
async def list_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> dict:
    """List all users in the admin's tenant. P2: full implementation."""
    tenant_id = admin.tenant_id

    count_stmt = (
        select(func.count())
        .select_from(User)
        .where(User.tenant_id == tenant_id)
    )
    total = (await session.execute(count_stmt)).scalar() or 0

    stmt = (
        select(User)
        .where(User.tenant_id == tenant_id)
        .order_by(User.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = (await session.execute(stmt)).scalars().all()

    items = [
        {
            "id": str(u.id),
            "email": u.email,
            "role": u.role.value,
            "tenant_id": str(u.tenant_id),
            "created_at": u.created_at.isoformat(),
        }
        for u in rows
    ]
    return paginate(items, total, page, page_size)
