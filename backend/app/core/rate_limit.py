"""Rate limiting middleware — token bucket per user/IP via Redis.

Returns 429 with X-RateLimit-* headers when the limit is exceeded.
Uses Redis INCR + EXPIRE for a simple sliding-window counter.
"""

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config import get_settings

# Paths excluded from rate limiting
_EXEMPT_PATHS = {"/api/v1/health", "/docs", "/openapi.json", "/redoc"}


def _get_client_id(request: Request) -> str:
    """Extract a rate-limit key: user_id from auth header, or client IP."""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        # Use last 8 chars of token as a crude user fingerprint
        # (actual user_id would require decoding the JWT)
        token_tail = auth[-16:]
        return f"user:{token_tail}"
    # Fall back to IP
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return f"ip:{forwarded.split(',')[0].strip()}"
    host = request.client.host if request.client else "unknown"
    return f"ip:{host}"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Redis-based rate limiter.

    Adds X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset headers.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Skip exempt paths
        if request.url.path in _EXEMPT_PATHS:
            return await call_next(request)

        settings = get_settings()
        limit = getattr(settings, "rate_limit_per_minute", 60)

        try:
            import redis.asyncio as aioredis

            client = aioredis.from_url(settings.redis_url)
            client_id = _get_client_id(request)
            key = f"rl:{client_id}"

            # Sliding window: INCR and set EXPIRE on first request
            current = await client.incr(key)
            if current == 1:
                await client.expire(key, 60)

            remaining = max(0, limit - current)
            reset = 60  # seconds

            if current > limit:
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": {
                            "code": "RATE_LIMIT",
                            "message": "Too many requests. Please try again later.",
                            "request_id": getattr(request.state, "request_id", None),
                        }
                    },
                    headers={
                        "X-RateLimit-Limit": str(limit),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(reset),
                    },
                )

            await client.aclose()
        except Exception:
            # If Redis is down, skip rate limiting (fail open)
            remaining = limit
            reset = 60

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset)
        return response
