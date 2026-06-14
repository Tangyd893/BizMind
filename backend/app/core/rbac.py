"""Role-based access control utilities."""

from app.core.exceptions import ForbiddenError
from app.models import User, UserRole


def require_role(user: User, *roles: UserRole) -> None:
    """Raise ForbiddenError if the user does not have one of the required roles."""
    if user.role not in roles:
        raise ForbiddenError(
            f"Required role(s): {', '.join(r.value for r in roles)}"
        )


def require_admin(user: User) -> None:
    """Raise ForbiddenError if the user is not an admin."""
    require_role(user, UserRole.ADMIN)
