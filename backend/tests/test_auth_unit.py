"""Auth service unit tests (JWT) without HTTP."""

import uuid
from datetime import UTC, datetime

from app.models import User, UserRole
from app.services.auth_service import _create_token


def test_create_token_contains_claims() -> None:
    user = User(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        email="jwt@test.com",
        password_hash="x",
        role=UserRole.USER,
        created_at=datetime.now(UTC),
    )
    token, expires_in = _create_token(user)
    assert isinstance(token, str)
    assert expires_in == 86400
