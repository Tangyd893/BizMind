from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse


class AppException(Exception):
    """Base application exception mapped to HTTP responses."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: list[dict[str, str]] | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or []
        super().__init__(message)


class UnauthorizedError(AppException):
    def __init__(self, message: str = "Unauthorized") -> None:
        super().__init__("UNAUTHORIZED", message, 401)


class ForbiddenError(AppException):
    def __init__(self, message: str = "Forbidden") -> None:
        super().__init__("FORBIDDEN", message, 403)


class NotFoundError(AppException):
    def __init__(self, message: str = "Not found") -> None:
        super().__init__("NOT_FOUND", message, 404)


class ConflictError(AppException):
    def __init__(self, message: str = "Conflict") -> None:
        super().__init__("CONFLICT", message, 409)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    body: dict[str, Any] = {
        "error": {
            "code": exc.code,
            "message": exc.message,
            "details": exc.details,
            "request_id": request_id,
        }
    }
    return JSONResponse(status_code=exc.status_code, content=body)
