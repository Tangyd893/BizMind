"""Unit tests for core helpers — no database required."""

import uuid

import pytest
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.core.pagination import paginate
from app.core.rbac import require_admin, require_role
from app.models import User, UserRole


def test_paginate_computes_pages() -> None:
    result = paginate(["a", "b"], total=25, page=2, page_size=10)
    assert result["pages"] == 3
    assert result["total"] == 25
    assert len(result["items"]) == 2


def test_paginate_empty_total() -> None:
    result = paginate([], total=0, page=1, page_size=20)
    assert result["pages"] == 1
    assert result["items"] == []


def test_exception_status_codes() -> None:
    assert ConflictError("dup").status_code == 409
    assert ForbiddenError().status_code == 403
    assert NotFoundError().status_code == 404


def test_require_role_raises_for_wrong_role() -> None:
    user = User(
        email="u@test.com",
        password_hash="x",
        role=UserRole.USER,
        tenant_id=uuid.uuid4(),
    )
    with pytest.raises(ForbiddenError):
        require_role(user, UserRole.ADMIN)


def test_require_admin_allows_admin() -> None:
    user = User(
        email="a@test.com",
        password_hash="x",
        role=UserRole.ADMIN,
        tenant_id=uuid.uuid4(),
    )
    require_admin(user)
